from flask import Blueprint

from app.controllers import user_skill_controller as ctrl
from app.middleware import roles_required

my_skills_bp = Blueprint("my_skills", __name__, url_prefix="/api/my/skills")


@my_skills_bp.route("/export", methods=["GET"])
@roles_required("seeker")
def export_my_skills():
    return ctrl.export_my_skills_csv()


@my_skills_bp.route("/import", methods=["POST"])
@roles_required("seeker")
def import_my_skills():
    return ctrl.import_my_skills_csv()


@my_skills_bp.route("", methods=["GET"])
@roles_required("seeker")
def get_my_skills():
    return ctrl.get_my_skills()


@my_skills_bp.route("", methods=["POST"])
@roles_required("seeker")
def create_my_skill():
    return ctrl.create_my_skill()


@my_skills_bp.route("/<int:user_skill_id>", methods=["PUT"])
@roles_required("seeker")
def update_my_skill(user_skill_id):
    return ctrl.update_my_skill(user_skill_id)


@my_skills_bp.route("/<int:user_skill_id>", methods=["DELETE"])
@roles_required("seeker")
def delete_my_skill(user_skill_id):
    return ctrl.delete_my_skill(user_skill_id)
