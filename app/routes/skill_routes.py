from flask import Blueprint

from app.controllers import skill_controller as ctrl
from app.middleware import require_role

skills_bp = Blueprint("skills", __name__, url_prefix="/api/skills")


@skills_bp.route("/export", methods=["GET"])
def export_skills():
    return ctrl.export_skills()


@skills_bp.route("/import", methods=["POST"])
@require_role("admin")
def import_skills():
    return ctrl.import_skills_csv()


@skills_bp.route("", methods=["GET"])
def get_skills():
    return ctrl.get_skills()


@skills_bp.route("", methods=["POST"])
@require_role("admin")
def create_skill():
    return ctrl.create_skill()


@skills_bp.route("/<int:skill_id>", methods=["GET"])
def get_skill(skill_id):
    return ctrl.get_skill(skill_id)


@skills_bp.route("/<int:skill_id>", methods=["PUT"])
@require_role("admin")
def update_skill(skill_id):
    return ctrl.update_skill(skill_id)


@skills_bp.route("/<int:skill_id>", methods=["DELETE"])
@require_role("admin")
def delete_skill(skill_id):
    return ctrl.delete_skill(skill_id)
