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


def create_skill():
    data = request.get_json(silent=True)
    errors = _validate_skill_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400
    try:
        skill = Skill(
            name=str(data.get("name")).strip(),
            category=(str(data.get("category")).strip() if data.get("category") else None),
            description=data.get("description"),
        )
        db.session.add(skill)
        db.session.commit()
        return jsonify({"message": "Skill created successfully.", "skill": skill.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def update_skill(skill_id):
    skill = db.session.get(Skill, skill_id)
    if not skill:
        return jsonify({"error": "Skill not found."}), 404
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400
    errors = _validate_skill_payload(data, skill_id=skill.id) if "name" in data else []
    if errors:
        return jsonify({"errors": errors}), 400
    try:
        if "name" in data:
            skill.name = str(data.get("name")).strip()
        if "category" in data:
            skill.category = str(data.get("category")).strip() if data.get("category") else None
        if "description" in data:
            skill.description = data.get("description")
        db.session.commit()
        return jsonify({"message": "Skill updated successfully.", "skill": skill.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def delete_skill(skill_id):
    skill = db.session.get(Skill, skill_id)
    if not skill:
        return jsonify({"error": "Skill not found."}), 404
    try:
        db.session.delete(skill)
        db.session.commit()
        return jsonify({"message": "Skill deleted successfully."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def export_skills():
    skills = Skill.query.order_by(Skill.name).all()
    headers = ["name", "category", "description"]
    rows = [[s.name, s.category or "", s.description or ""] for s in skills]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if (request.args.get("format") or "csv").lower() == "pdf":
        return table_pdf_response(f"skills-{today}.pdf", "Skills Catalog", headers, rows)
    return rows_to_csv_response(f"skills-{today}.csv", headers, rows)


def import_skills_csv():
    file = request.files.get("file")
    rows, header_errors = parse_csv_file(file, ["name", "category", "description"])
    if header_errors:
        return jsonify({"errors": header_errors}), 400

    created = skipped = 0
    errors = []
    try:
        for i, row in enumerate(rows, start=2):
            name = (row.get("name") or "").strip()
            if not name:
                errors.append({"row": i, "message": "name is required."})
                continue
            if Skill.query.filter_by(name=name).first():
                skipped += 1
                continue
            db.session.add(
                Skill(
                    name=name,
                    category=(row.get("category") or "").strip() or None,
                    description=(row.get("description") or "").strip() or None,
                )
            )
            created += 1
        db.session.commit()
        return jsonify({"created": created, "skipped": skipped, "errors": errors}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
