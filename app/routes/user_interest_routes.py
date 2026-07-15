from flask import Blueprint

from app.controllers import user_interest_controller as ctrl
from app.middleware import jwt_required_active

my_interests_bp = Blueprint("my_interests", __name__, url_prefix="/api/my/interests")


@my_interests_bp.route("", methods=["GET"])
@jwt_required_active
def get_my_interests():
    return ctrl.get_my_interests()


@my_interests_bp.route("", methods=["POST"])
@jwt_required_active
def create_my_interest():
    return ctrl.create_my_interest()


@my_interests_bp.route("/<int:user_interest_id>", methods=["DELETE"])
@jwt_required_active
def delete_my_interest(user_interest_id):
    return ctrl.delete_my_interest(user_interest_id)
