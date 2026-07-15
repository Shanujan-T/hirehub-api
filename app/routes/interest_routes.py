from flask import Blueprint

from app.controllers import interest_controller as ctrl
from app.middleware import require_role

interests_bp = Blueprint("interests", __name__, url_prefix="/api/interests")


@interests_bp.route("", methods=["GET"])
def get_interests():
    return ctrl.get_interests()


@interests_bp.route("", methods=["POST"])
@require_role("admin")
def create_interest():
    return ctrl.create_interest()


@interests_bp.route("/<int:interest_id>", methods=["GET"])
def get_interest(interest_id):
    return ctrl.get_interest(interest_id)


@interests_bp.route("/<int:interest_id>", methods=["PUT"])
@require_role("admin")
def update_interest(interest_id):
    return ctrl.update_interest(interest_id)


@interests_bp.route("/<int:interest_id>", methods=["DELETE"])
@require_role("admin")
def delete_interest(interest_id):
    return ctrl.delete_interest(interest_id)
