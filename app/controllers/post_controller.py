from flask import jsonify, request
from flask_jwt_extended import current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Comment, Job, Post
from app.models.post_model import POST_TYPES


def get_posts():
    q = (request.args.get("q") or "").strip().lower()
    post_type = (request.args.get("type") or "").strip().lower()
    query = Post.query
    if q:
        query = query.filter(or_(Post.title.ilike(f"%{q}%"), Post.body.ilike(f"%{q}%")))
    if post_type:
        query = query.filter(Post.type == post_type)
    posts = query.order_by(Post.id.desc()).all()
    return jsonify({"posts": [p.to_dict() for p in posts]}), 200


def get_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({"error": "Post not found."}), 404
    return jsonify({"post": post.to_dict(include_comments=True)}), 200


def create_post():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    errors = []
    title = str(data.get("title") or "").strip()
    body = str(data.get("body") or "").strip()
    post_type = str(data.get("type") or "discussion").strip().lower()
    job_id = data.get("job_id")

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

    try:
        post = Post(
            author_id=current_user.id,
            title=title,
            body=body,
            type=post_type,
            job_id=job_id,
        )
        db.session.add(post)
        db.session.commit()
        return jsonify({"message": "Post created.", "post": post.to_dict()}), 201
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
        db.session.commit()
        return jsonify({"message": "Post updated.", "post": post.to_dict()}), 200
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
    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.id.asc()).all()
    return jsonify({"comments": [c.to_dict() for c in comments]}), 200


def create_comment(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({"error": "Post not found."}), 404
    data = request.get_json(silent=True)
    if not data or not str(data.get("body") or "").strip():
        return jsonify({"errors": ["body is required."]}), 400
    try:
        comment = Comment(
            post_id=post.id,
            author_id=current_user.id,
            body=str(data.get("body")).strip(),
        )
        db.session.add(comment)
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
