from flask import Blueprint

from app.controllers import auth_controller as auth_ctrl
from app.controllers import dashboard_controller as ctrl
from app.middleware import jwt_required_active, roles_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/me")


@dashboard_bp.route("/resume", methods=["POST"])
@roles_required("seeker")
def upload_resume():
    return auth_ctrl.upload_resume()


@dashboard_bp.route("/avatar", methods=["POST"])
@jwt_required_active
def upload_avatar():
    return auth_ctrl.upload_avatar()


@dashboard_bp.route("/dashboard", methods=["GET"])
@jwt_required_active
def get_dashboard():
    return ctrl.get_dashboard()


@dashboard_bp.route("/dashboard/pdf", methods=["GET"])
@jwt_required_active
def export_dashboard_pdf():
    return ctrl.export_dashboard_pdf()
