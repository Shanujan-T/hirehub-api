from flask import Blueprint

from app.controllers import post_controller as ctrl
from app.middleware import jwt_required_active, roles_required

posts_bp = Blueprint("posts", __name__, url_prefix="/api/posts")
comments_bp = Blueprint("comments", __name__, url_prefix="/api/comments")


@posts_bp.route("", methods=["GET"])
def get_posts():
    return ctrl.get_posts()


@posts_bp.route("", methods=["POST"])
@jwt_required_active
def create_post():
    return ctrl.create_post()


@posts_bp.route("/<int:post_id>/image", methods=["POST"])
@jwt_required_active
def upload_post_image(post_id):
    return ctrl.upload_post_image(post_id)


@posts_bp.route("/<int:post_id>", methods=["GET"])
def get_post(post_id):
    return ctrl.get_post(post_id)


@posts_bp.route("/<int:post_id>", methods=["PUT"])
@jwt_required_active
def update_post(post_id):
    return ctrl.update_post(post_id)


@posts_bp.route("/<int:post_id>", methods=["DELETE"])
@jwt_required_active
def delete_post(post_id):
    return ctrl.delete_post(post_id)


@posts_bp.route("/<int:post_id>/comments", methods=["GET"])
def get_post_comments(post_id):
    return ctrl.get_post_comments(post_id)


@posts_bp.route("/<int:post_id>/comments", methods=["POST"])
@jwt_required_active
def create_comment(post_id):
    return ctrl.create_comment(post_id)


@comments_bp.route("/<int:comment_id>", methods=["DELETE"])
@jwt_required_active
def delete_comment(comment_id):
    return ctrl.delete_comment(comment_id)


@posts_bp.route("/<int:post_id>/reactions", methods=["POST"])
@jwt_required_active
def add_reaction(post_id):
    return ctrl.add_reaction(post_id)


@posts_bp.route("/<int:post_id>/reactions", methods=["DELETE"])
@jwt_required_active
def remove_reaction(post_id):
    return ctrl.remove_reaction(post_id)


@posts_bp.route("/<int:post_id>/bookmark", methods=["POST"])
@jwt_required_active
def bookmark_post(post_id):
    return ctrl.bookmark_post(post_id)


@posts_bp.route("/<int:post_id>/bookmark", methods=["DELETE"])
@jwt_required_active
def unbookmark_post(post_id):
    return ctrl.unbookmark_post(post_id)


my_bookmarks_bp = Blueprint("my_bookmarks", __name__, url_prefix="/api/my")


@my_bookmarks_bp.route("/bookmarks", methods=["GET"])
@jwt_required_active
def get_my_bookmarks():
    return ctrl.get_my_bookmarks()
