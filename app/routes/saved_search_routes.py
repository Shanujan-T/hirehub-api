from flask import Blueprint

from app.controllers import saved_search_controller as ctrl
from app.middleware import jwt_required_active

my_saved_searches_bp = Blueprint(
    "my_saved_searches", __name__, url_prefix="/api/my/saved-searches"
)


@my_saved_searches_bp.route("", methods=["GET"])
@jwt_required_active
def get_my_saved_searches():
    return ctrl.get_my_saved_searches()


@my_saved_searches_bp.route("", methods=["POST"])
@jwt_required_active
def create_my_saved_search():
    return ctrl.create_my_saved_search()


@my_saved_searches_bp.route("/<int:saved_search_id>", methods=["GET"])
@jwt_required_active
def get_my_saved_search(saved_search_id):
    return ctrl.get_my_saved_search(saved_search_id)


@my_saved_searches_bp.route("/<int:saved_search_id>", methods=["PUT"])
@jwt_required_active
def update_my_saved_search(saved_search_id):
    return ctrl.update_my_saved_search(saved_search_id)


@my_saved_searches_bp.route("/<int:saved_search_id>", methods=["DELETE"])
@jwt_required_active
def delete_my_saved_search(saved_search_id):
    return ctrl.delete_my_saved_search(saved_search_id)
