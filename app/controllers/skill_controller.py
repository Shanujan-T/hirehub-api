from datetime import datetime

from flask import jsonify, request

from app.extensions import db
from app.models import Skill
from app.utils.csv_utils import parse_csv_file, rows_to_csv_response
from app.utils.pdf_utils import table_pdf_response


def _validate_skill_payload(data, skill_id=None):
    errors = []
    if not data:
        return ["Request body is required."]
    name = data.get("name")
    if name is None or str(name).strip() == "":
        errors.append("name is required.")
    else:
        existing = Skill.query.filter_by(name=str(name).strip()).first()
        if existing and (skill_id is None or existing.id != skill_id):
            errors.append("Skill name already exists.")
    return errors


def get_skills():
    q = (request.args.get("q") or "").strip().lower()
    category = (request.args.get("category") or "").strip().lower()
    query = Skill.query
    if q:
        query = query.filter(Skill.name.ilike(f"%{q}%"))
    if category:
        query = query.filter(Skill.category.ilike(f"%{category}%"))
    return jsonify({"skills": [s.to_dict() for s in query.order_by(Skill.name).all()]}), 200


def get_skill(skill_id):
    skill = db.session.get(Skill, skill_id)
    if not skill:
        return jsonify({"error": "Skill not found."}), 404
    return jsonify({"skill": skill.to_dict()}), 200
