from flask import Blueprint

from app.controllers import job_controller as ctrl
from app.middleware import require_role, roles_required

jobs_bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")
my_saved_jobs_bp = Blueprint("my_saved_jobs", __name__, url_prefix="/api/my")


@jobs_bp.route("/recommended", methods=["GET"])
@roles_required("seeker")
def recommended():
    return ctrl.get_recommended_jobs()


@jobs_bp.route("/export", methods=["GET"])
@roles_required("employer", "admin")
def export_jobs():
    return ctrl.export_jobs()


@jobs_bp.route("/import", methods=["POST"])
@roles_required("employer")
def import_jobs():
    return ctrl.import_jobs_csv()


@jobs_bp.route("", methods=["GET"])
def get_jobs():
    return ctrl.get_jobs()


@jobs_bp.route("", methods=["POST"])
@roles_required("employer")
def create_job():
    return ctrl.create_job()


@jobs_bp.route("/<int:job_id>/pdf", methods=["GET"])
def export_job_pdf(job_id):
    return ctrl.export_job_pdf(job_id)


@jobs_bp.route("/<int:job_id>/applications", methods=["GET"])
@roles_required("employer", "admin")
def get_job_applications(job_id):
    return ctrl.get_job_applications(job_id)


@jobs_bp.route("/<int:job_id>/save", methods=["POST"])
@roles_required("seeker")
def save_job(job_id):
    return ctrl.save_job(job_id)


@jobs_bp.route("/<int:job_id>/save", methods=["DELETE"])
@roles_required("seeker")
def unsave_job(job_id):
    return ctrl.unsave_job(job_id)


@jobs_bp.route("/<int:job_id>/status", methods=["PATCH"])
@roles_required("employer", "admin")
def patch_job_status(job_id):
    return ctrl.patch_job_status(job_id)


@jobs_bp.route("/<int:job_id>", methods=["GET"])
def get_job(job_id):
    return ctrl.get_job(job_id)


@jobs_bp.route("/<int:job_id>", methods=["PUT"])
@roles_required("employer", "admin")
def update_job(job_id):
    return ctrl.update_job(job_id)


@jobs_bp.route("/<int:job_id>", methods=["DELETE"])
@roles_required("employer", "admin")
def delete_job(job_id):
    return ctrl.delete_job(job_id)


@my_saved_jobs_bp.route("/saved-jobs", methods=["GET"])
@roles_required("seeker")
def get_my_saved_jobs():
    return ctrl.get_my_saved_jobs()
