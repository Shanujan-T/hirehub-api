from flask import Blueprint

from app.controllers import community_controller as ctrl
from app.middleware import jwt_required_active

communities_bp = Blueprint("communities", __name__, url_prefix="/api/communities")
my_communities_bp = Blueprint("my_communities", __name__, url_prefix="/api/my")


@communities_bp.route("", methods=["GET"])
def list_communities():
    return ctrl.get_communities()


@communities_bp.route("", methods=["POST"])
@jwt_required_active
def create_community():
    return ctrl.create_community()


@my_communities_bp.route("/communities", methods=["GET"])
@jwt_required_active
def my_communities():
    return ctrl.get_my_communities()


@communities_bp.route("/<int:community_id>", methods=["GET"])
def get_community(community_id):
    return ctrl.get_community(community_id)


@communities_bp.route("/<int:community_id>", methods=["PUT"])
@jwt_required_active
def update_community(community_id):
    return ctrl.update_community(community_id)


@communities_bp.route("/<int:community_id>", methods=["DELETE"])
@jwt_required_active
def delete_community(community_id):
    return ctrl.delete_community(community_id)


@communities_bp.route("/<int:community_id>/join", methods=["POST"])
@jwt_required_active
def join_community(community_id):
    return ctrl.join_community(community_id)


@communities_bp.route("/<int:community_id>/leave", methods=["POST"])
@jwt_required_active
def leave_community(community_id):
    return ctrl.leave_community(community_id)


@communities_bp.route("/<int:community_id>/members", methods=["GET"])
def get_members(community_id):
    return ctrl.get_community_members(community_id)


@communities_bp.route("/<int:community_id>/members/<int:user_id>", methods=["PATCH"])
@jwt_required_active
def update_member(community_id, user_id):
    return ctrl.update_member_role(community_id, user_id)


@communities_bp.route("/<int:community_id>/members/<int:user_id>", methods=["DELETE"])
@jwt_required_active
def remove_member(community_id, user_id):
    return ctrl.remove_member(community_id, user_id)


@communities_bp.route("/<int:community_id>/feed", methods=["GET"])
def community_feed(community_id):
    return ctrl.get_community_feed(community_id)


@communities_bp.route("/<int:community_id>/announcements", methods=["GET"])
def get_announcements(community_id):
    return ctrl.get_announcements(community_id)


@communities_bp.route("/<int:community_id>/announcements", methods=["POST"])
@jwt_required_active
def create_announcement(community_id):
    return ctrl.create_announcement(community_id)


@communities_bp.route("/<int:community_id>/announcements/<int:announcement_id>", methods=["PUT"])
@jwt_required_active
def update_announcement(community_id, announcement_id):
    return ctrl.update_announcement(community_id, announcement_id)


@communities_bp.route("/<int:community_id>/announcements/<int:announcement_id>", methods=["DELETE"])
@jwt_required_active
def delete_announcement(community_id, announcement_id):
    return ctrl.delete_announcement(community_id, announcement_id)
