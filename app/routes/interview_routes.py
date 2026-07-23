from flask import Blueprint

from app.controllers import interview_controller as ctrl
from app.middleware import roles_required

interviews_bp = Blueprint("interviews", __name__, url_prefix="/api/interviews")


@interviews_bp.route("/<int:interview_id>/select", methods=["PATCH"])
@roles_required("seeker")
def select_interview_slot(interview_id):
    return ctrl.select_interview_slot(interview_id)


@interviews_bp.route("/<int:interview_id>/cancel", methods=["PATCH"])
@roles_required("seeker", "employer")
def cancel_interview(interview_id):
    return ctrl.cancel_interview(interview_id)
