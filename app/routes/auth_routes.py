from flask import Blueprint

from app.controllers import auth_controller as ctrl

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    return ctrl.register()


@auth_bp.route("/login", methods=["POST"])
def login():
    return ctrl.login()


