from flask import Blueprint

from app.controllers import mentorship_controller as ctrl
from app.middleware import jwt_required_active

mentorships_bp = Blueprint("mentorships", __name__, url_prefix="/api/mentorships")
my_mentorships_bp = Blueprint("my_mentorships", __name__, url_prefix="/api/my")
mentors_bp = Blueprint("mentors", __name__, url_prefix="/api/mentors")


@mentorships_bp.route("", methods=["POST"])
@jwt_required_active
def create_mentorship():
    return ctrl.create_mentorship()


@my_mentorships_bp.route("/mentorships", methods=["GET"])
@jwt_required_active
def get_my_mentorships():
    return ctrl.get_my_mentorships()


@mentors_bp.route("", methods=["GET"])
def discover_mentors():
    return ctrl.discover_mentors()


@my_mentorships_bp.route("/mentor-profile", methods=["PUT"])
@jwt_required_active
def upsert_mentor_profile():
    return ctrl.upsert_mentor_profile()


@mentors_bp.route("/<int:user_id>", methods=["GET"])
def get_mentor_profile(user_id):
    return ctrl.get_mentor_profile(user_id)


@mentorships_bp.route("/<int:mentorship_id>/accept", methods=["PATCH"])
@jwt_required_active
def accept(mentorship_id):
    return ctrl.accept_mentorship(mentorship_id)


@mentorships_bp.route("/<int:mentorship_id>/decline", methods=["PATCH"])
@jwt_required_active
def decline(mentorship_id):
    return ctrl.decline_mentorship(mentorship_id)


@mentorships_bp.route("/<int:mentorship_id>/end", methods=["PATCH"])
@jwt_required_active
def end(mentorship_id):
    return ctrl.end_mentorship(mentorship_id)


@mentorships_bp.route("/<int:mentorship_id>/sessions", methods=["POST"])
@jwt_required_active
def create_session(mentorship_id):
    return ctrl.create_session(mentorship_id)


@mentorships_bp.route("/<int:mentorship_id>/sessions/<int:session_id>", methods=["PATCH"])
@jwt_required_active
def update_session(mentorship_id, session_id):
    return ctrl.update_session(mentorship_id, session_id)
