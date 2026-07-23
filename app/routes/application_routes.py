from flask import Blueprint

from app.controllers import application_controller as ctrl
from app.controllers import interview_controller as interview_ctrl
from app.middleware import require_role, roles_required

applications_bp = Blueprint("applications", __name__, url_prefix="/api/applications")


@applications_bp.route("/my", methods=["GET"])
@roles_required("seeker")
def get_my_applications():
    return ctrl.get_my_applications()


@applications_bp.route("/export", methods=["GET"])
@roles_required("seeker", "employer", "admin")
def export_applications():
    return ctrl.export_applications_csv()


@applications_bp.route("", methods=["GET"])
@require_role("admin")
def get_applications():
    return ctrl.get_applications()


@applications_bp.route("", methods=["POST"])
@roles_required("seeker")
def create_application():
    return ctrl.create_application()


@applications_bp.route("/<int:application_id>/pdf", methods=["GET"])
@roles_required("seeker", "employer", "admin")
def export_application_pdf(application_id):
    return ctrl.export_application_pdf(application_id)


@applications_bp.route("/<int:application_id>/shortlist", methods=["PATCH"])
@roles_required("employer")
def shortlist(application_id):
    return ctrl.shortlist_application(application_id)


@applications_bp.route("/<int:application_id>/accept", methods=["PATCH"])
@roles_required("employer")
def accept(application_id):
    return ctrl.accept_application(application_id)


@applications_bp.route("/<int:application_id>/reject", methods=["PATCH"])
@roles_required("employer")
def reject(application_id):
    return ctrl.reject_application(application_id)


@applications_bp.route("/<int:application_id>/withdraw", methods=["PATCH"])
@roles_required("seeker")
def withdraw(application_id):
    return ctrl.withdraw_application(application_id)


@applications_bp.route("/<int:application_id>/history", methods=["GET"])
@roles_required("seeker", "employer", "admin")
def get_application_history(application_id):
    return ctrl.get_application_history(application_id)


@applications_bp.route("/<int:application_id>/interview", methods=["GET"])
@roles_required("seeker", "employer", "admin")
def get_application_interview(application_id):
    return interview_ctrl.get_application_interview(application_id)


@applications_bp.route("/<int:application_id>/interview", methods=["POST"])
@roles_required("employer")
def propose_application_interview(application_id):
    return interview_ctrl.propose_interview(application_id)


@applications_bp.route("/<int:application_id>", methods=["GET"])
@roles_required("seeker", "employer", "admin")
def get_application(application_id):
    return ctrl.get_application(application_id)


@applications_bp.route("/<int:application_id>", methods=["DELETE"])
@require_role("admin")
def delete_application(application_id):
    return ctrl.delete_application(application_id)
