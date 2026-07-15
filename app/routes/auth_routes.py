from flask import Blueprint

from app.controllers import auth_controller as ctrl
from app.middleware import jwt_required_active

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    return ctrl.register()


@auth_bp.route("/login", methods=["POST"])
def login():
    return ctrl.login()


@auth_bp.route("/logout", methods=["POST"])
@jwt_required_active
def logout():
    return ctrl.logout()


@auth_bp.route("/profile", methods=["GET"])
@jwt_required_active
def get_profile():
    return ctrl.get_profile()


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required_active
def update_profile():
    return ctrl.update_profile()
