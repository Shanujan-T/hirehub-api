from flask import Blueprint

from app.controllers import company_controller as ctrl
from app.middleware import require_role, roles_required

companies_bp = Blueprint("companies", __name__, url_prefix="/api/companies")
my_company_bp = Blueprint("my_company", __name__, url_prefix="/api/my")


@companies_bp.route("/export", methods=["GET"])
@require_role("admin")
def export_companies():
    return ctrl.export_companies_csv()


@companies_bp.route("", methods=["GET"])
def get_companies():
    return ctrl.get_companies()


@companies_bp.route("", methods=["POST"])
@roles_required("employer")
def create_company():
    return ctrl.create_company()


@companies_bp.route("/<int:company_id>/verify", methods=["PATCH"])
@require_role("admin")
def verify_company(company_id):
    return ctrl.verify_company(company_id)


@companies_bp.route("/<int:company_id>/logo", methods=["POST"])
@roles_required("employer", "admin")
def upload_company_logo(company_id):
    return ctrl.upload_company_logo(company_id)


@companies_bp.route("/<int:company_id>", methods=["GET"])
def get_company(company_id):
    return ctrl.get_company(company_id)


@companies_bp.route("/<int:company_id>", methods=["PUT"])
@roles_required("employer", "admin")
def update_company(company_id):
    return ctrl.update_company(company_id)


@companies_bp.route("/<int:company_id>", methods=["DELETE"])
@require_role("admin")
def delete_company(company_id):
    return ctrl.delete_company(company_id)


@my_company_bp.route("/company", methods=["GET"])
@roles_required("employer")
def get_my_company():
    return ctrl.get_my_company()
