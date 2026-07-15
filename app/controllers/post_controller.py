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
