from flask import jsonify, request

from flask_jwt_extended import current_user

from sqlalchemy import or_



from app.extensions import db

from app.models import Comment, Community, Job, Post, PostBookmark, PostReaction

from app.models.post_model import POST_TYPES

from app.models.post_reaction_model import REACTION_TYPES

from app.utils.social_helpers import (

    extract_hashtags,

    get_membership,

    is_community_member,

    sync_hashtags,

    sync_mentions_comment,

    sync_mentions_post,

    sync_post_media,

)





def get_posts():

    q = (request.args.get("q") or "").strip().lower()

    post_type = (request.args.get("type") or "").strip().lower()

    community_id = request.args.get("community_id")

    hashtag = (request.args.get("hashtag") or "").strip().lower().lstrip("#")



    query = Post.query

    if q:

        query = query.filter(or_(Post.title.ilike(f"%{q}%"), Post.body.ilike(f"%{q}%")))

    if post_type:

        query = query.filter(Post.type == post_type)

    if community_id:

        query = query.filter(Post.community_id == int(community_id))

    if hashtag:
        from app.models import Hashtag

        query = query.join(Post.hashtags).filter(Hashtag.name == hashtag)



    posts = query.order_by(Post.id.desc()).all()

    return jsonify({"posts": [p.to_dict(include_details=True) for p in posts]}), 200





def get_post(post_id):

    post = db.session.get(Post, post_id)

    if not post:

        return jsonify({"error": "Post not found."}), 404

    return jsonify({"post": post.to_dict(include_comments=True, include_details=True)}), 200





def _validate_community_post(community_id):

    if not community_id:

        return None

    community = db.session.get(Community, community_id)

    if not community:

        return jsonify({"errors": ["community_id not found."]}), 400

    membership = get_membership(current_user.id, community_id)

    if not is_community_member(membership):

        return jsonify({"error": "Join the community before posting."}), 403

    return None





def create_post():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({"error": "Request body is required."}), 400



    errors = []

    title = str(data.get("title") or "").strip()

    body = str(data.get("body") or "").strip()

    post_type = str(data.get("type") or "discussion").strip().lower()

    job_id = data.get("job_id")

    community_id = data.get("community_id")



    if not title:

        errors.append("title is required.")

    if not body:

        errors.append("body is required.")

    if post_type not in POST_TYPES:

        errors.append(f"type must be one of: {', '.join(POST_TYPES)}.")

    if job_id is not None and job_id != "":

        if not db.session.get(Job, job_id):

            errors.append("job_id not found.")

    else:

        job_id = None



    if errors:

        return jsonify({"errors": errors}), 400



    community_err = _validate_community_post(community_id)

    if community_err:

        return community_err



    try:

        post = Post(

            author_id=current_user.id,

            community_id=community_id,

            title=title,

            body=body,

            type=post_type,

            job_id=job_id,

            link_url=data.get("link_url"),

        )

        db.session.add(post)

        db.session.flush()



        hashtag_names = data.get("hashtags") or extract_hashtags(body)

        sync_hashtags(post, hashtag_names)

        sync_post_media(post, data.get("media"))

        sync_mentions_post(post, data.get("mention_user_ids"))



        db.session.commit()

        return jsonify({"message": "Post created.", "post": post.to_dict(include_details=True)}), 201

    except Exception:

        db.session.rollback()

        return jsonify({"error": "An internal server error occurred."}), 500





def update_post(post_id):

    post = db.session.get(Post, post_id)

    if not post:

        return jsonify({"error": "Post not found."}), 404

    if post.author_id != current_user.id and current_user.role != "admin":

        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403



    data = request.get_json(silent=True)

    if not data:

        return jsonify({"error": "Request body is required."}), 400



    try:

        if "title" in data:

            title = str(data.get("title") or "").strip()

            if not title:

                return jsonify({"errors": ["title cannot be empty."]}), 400

            post.title = title

        if "body" in data:

            body = str(data.get("body") or "").strip()

            if not body:

                return jsonify({"errors": ["body cannot be empty."]}), 400

            post.body = body

        if "type" in data:

            post_type = str(data.get("type")).strip().lower()

            if post_type not in POST_TYPES:

                return jsonify({"errors": [f"type must be one of: {', '.join(POST_TYPES)}."]}), 400

            post.type = post_type

        if "job_id" in data:

            job_id = data.get("job_id")

            if job_id in (None, ""):

                post.job_id = None

            elif not db.session.get(Job, job_id):

                return jsonify({"errors": ["job_id not found."]}), 400

            else:

                post.job_id = job_id

        if "link_url" in data:

            post.link_url = data.get("link_url")

        if "hashtags" in data or "body" in data:

            sync_hashtags(post, data.get("hashtags") or extract_hashtags(post.body))

        if "media" in data:

            sync_post_media(post, data.get("media"))

        if "mention_user_ids" in data:

            sync_mentions_post(post, data.get("mention_user_ids"))

        db.session.commit()

        return jsonify({"message": "Post updated.", "post": post.to_dict(include_details=True)}), 200

    except Exception:

        db.session.rollback()

        return jsonify({"error": "An internal server error occurred."}), 500





def delete_post(post_id):

    post = db.session.get(Post, post_id)

    if not post:

        return jsonify({"error": "Post not found."}), 404

    if post.author_id != current_user.id and current_user.role != "admin":

        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    try:

        db.session.delete(post)

        db.session.commit()

        return jsonify({"message": "Post deleted."}), 200

    except Exception:

        db.session.rollback()

        return jsonify({"error": "An internal server error occurred."}), 500





def get_post_comments(post_id):

    post = db.session.get(Post, post_id)

    if not post:

        return jsonify({"error": "Post not found."}), 404

    comments = Comment.query.filter_by(post_id=post.id, parent_id=None).order_by(

        Comment.id.asc()

    ).all()

    return jsonify({"comments": [c.to_dict(include_replies=True) for c in comments]}), 200





def create_comment(post_id):

    post = db.session.get(Post, post_id)

    if not post:

        return jsonify({"error": "Post not found."}), 404

    data = request.get_json(silent=True)

    if not data or not str(data.get("body") or "").strip():

        return jsonify({"errors": ["body is required."]}), 400



    parent_id = data.get("parent_id")

    if parent_id:

        parent = db.session.get(Comment, parent_id)

        if not parent or parent.post_id != post.id:

            return jsonify({"errors": ["parent_id not found for this post."]}), 400



    try:

        comment = Comment(

            post_id=post.id,

            author_id=current_user.id,

            parent_id=parent_id,

            body=str(data.get("body")).strip(),

        )

        db.session.add(comment)

        db.session.flush()

        sync_mentions_comment(comment, data.get("mention_user_ids"))

        db.session.commit()

        return jsonify({"message": "Comment created.", "comment": comment.to_dict()}), 201

    except Exception:

        db.session.rollback()

        return jsonify({"error": "An internal server error occurred."}), 500





def delete_comment(comment_id):

    comment = db.session.get(Comment, comment_id)

    if not comment:

        return jsonify({"error": "Comment not found."}), 404

    if comment.author_id != current_user.id and current_user.role != "admin":

        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    try:

        db.session.delete(comment)

        db.session.commit()

        return jsonify({"message": "Comment deleted."}), 200

    except Exception:

        db.session.rollback()

        return jsonify({"error": "An internal server error occurred."}), 500





def add_reaction(post_id):

    post = db.session.get(Post, post_id)

    if not post:

        return jsonify({"error": "Post not found."}), 404



    data = request.get_json(silent=True) or {}

    reaction_type = str(data.get("reaction_type") or "like").strip().lower()

    if reaction_type not in REACTION_TYPES:

        return jsonify({"errors": [f"reaction_type must be one of: {', '.join(REACTION_TYPES)}."]}), 400



    existing = PostReaction.query.filter_by(post_id=post.id, user_id=current_user.id).first()

    try:

        if existing:

            existing.reaction_type = reaction_type

            row = existing

        else:

            row = PostReaction(

                post_id=post.id,

                user_id=current_user.id,

                reaction_type=reaction_type,

            )

            db.session.add(row)

        db.session.commit()

        return jsonify({"message": "Reaction saved.", "reaction": row.to_dict()}), 200

    except Exception:

        db.session.rollback()

        return jsonify({"error": "An internal server error occurred."}), 500





def remove_reaction(post_id):

    row = PostReaction.query.filter_by(post_id=post_id, user_id=current_user.id).first()

    if not row:

        return jsonify({"error": "Reaction not found."}), 404

    try:

        db.session.delete(row)

        db.session.commit()

        return jsonify({"message": "Reaction removed."}), 200

    except Exception:

        db.session.rollback()

        return jsonify({"error": "An internal server error occurred."}), 500





def bookmark_post(post_id):

    post = db.session.get(Post, post_id)

    if not post:

        return jsonify({"error": "Post not found."}), 404

    if PostBookmark.query.filter_by(user_id=current_user.id, post_id=post.id).first():

        return jsonify({"error": "Post already bookmarked."}), 400

    try:

        row = PostBookmark(user_id=current_user.id, post_id=post.id)

        db.session.add(row)

        db.session.commit()

        return jsonify({"message": "Post bookmarked.", "bookmark": row.to_dict()}), 201

    except Exception:

        db.session.rollback()

        return jsonify({"error": "An internal server error occurred."}), 500





def unbookmark_post(post_id):

    row = PostBookmark.query.filter_by(user_id=current_user.id, post_id=post_id).first()

    if not row:

        return jsonify({"error": "Bookmark not found."}), 404

    try:

        db.session.delete(row)

        db.session.commit()

        return jsonify({"message": "Bookmark removed."}), 200

    except Exception:

        db.session.rollback()

        return jsonify({"error": "An internal server error occurred."}), 500





def get_my_bookmarks():

    rows = PostBookmark.query.filter_by(user_id=current_user.id).order_by(

        PostBookmark.id.desc()

    ).all()

    return jsonify({"bookmarks": [r.to_dict() for r in rows]}), 200


