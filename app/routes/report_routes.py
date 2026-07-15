from flask import Blueprint

from app.controllers import report_controller as ctrl
from app.middleware import jwt_required_active, require_role

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@reports_bp.route("", methods=["POST"])
@jwt_required_active
def create_report():
    return ctrl.create_report()


@reports_bp.route("", methods=["GET"])
@require_role("admin")
def get_reports():
    return ctrl.get_reports()


@reports_bp.route("/<int:report_id>", methods=["GET"])
@require_role("admin")
def get_report(report_id):
    return ctrl.get_report(report_id)


@reports_bp.route("/<int:report_id>/resolve", methods=["PATCH"])
@require_role("admin")
def resolve_report(report_id):
    return ctrl.resolve_report(report_id)
