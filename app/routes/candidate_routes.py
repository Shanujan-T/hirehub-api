from flask import Blueprint

from app.controllers import candidate_controller as ctrl
from app.middleware import roles_required

candidates_bp = Blueprint("candidates", __name__, url_prefix="/api/candidates")


@candidates_bp.route("", methods=["GET"])
@roles_required("employer", "admin")
def get_candidates():
    return ctrl.get_candidates()


@candidates_bp.route("/<int:candidate_id>/pdf", methods=["GET"])
@roles_required("employer", "admin")
def export_candidate_pdf(candidate_id):
    return ctrl.export_candidate_pdf(candidate_id)


@candidates_bp.route("/<int:candidate_id>", methods=["GET"])
@roles_required("employer", "admin")
def get_candidate(candidate_id):
    return ctrl.get_candidate(candidate_id)
