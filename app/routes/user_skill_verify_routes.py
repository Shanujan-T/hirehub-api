from flask import Blueprint

from app.controllers import user_skill_controller as ctrl
from app.middleware import roles_required

user_skills_bp = Blueprint("user_skills", __name__, url_prefix="/api/user-skills")


@user_skills_bp.route("/<int:user_skill_id>/verify", methods=["PATCH"])
@roles_required("employer")
def verify_user_skill(user_skill_id):
    return ctrl.verify_user_skill(user_skill_id)
