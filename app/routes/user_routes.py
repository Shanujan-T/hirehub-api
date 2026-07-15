from flask import Blueprint

from app.controllers import user_controller as ctrl
from app.middleware import require_role, roles_required

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.route("/export", methods=["GET"])
@require_role("admin")
def export_users():
    return ctrl.export_users_csv()


@users_bp.route("/import", methods=["POST"])
@require_role("admin")
def import_users():
    return ctrl.import_users_csv()


@users_bp.route("", methods=["GET"])
@require_role("admin")
def get_users():
    return ctrl.get_users()


@users_bp.route("/<int:user_id>", methods=["GET"])
@roles_required("admin", "seeker", "employer")
def get_user(user_id):
    return ctrl.get_user(user_id)


@users_bp.route("/<int:user_id>", methods=["PUT"])
@roles_required("admin", "seeker", "employer")
def update_user(user_id):
    return ctrl.update_user(user_id)


@users_bp.route("/<int:user_id>/status", methods=["PATCH"])
@require_role("admin")
def patch_user_status(user_id):
    return ctrl.patch_user_status(user_id)


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@require_role("admin")
def delete_user(user_id):
    return ctrl.delete_user(user_id)
