from datetime import datetime

from flask import jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Application, Job, Skill, UserSkill
from app.models.user_skill_model import SKILL_LEVELS
from app.utils.csv_utils import parse_csv_file, rows_to_csv_response


def get_my_skills():
    rows = UserSkill.query.filter_by(user_id=current_user.id).order_by(UserSkill.id.desc()).all()
    return jsonify({"user_skills": [r.to_dict() for r in rows]}), 200


def create_my_skill():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    errors = []
    skill_id = data.get("skill_id")
    level = str(data.get("level") or "beginner").strip().lower()
    if not skill_id:
        errors.append("skill_id is required.")
    if level not in SKILL_LEVELS:
        errors.append(f"level must be one of: {', '.join(SKILL_LEVELS)}.")
    skill = db.session.get(Skill, skill_id) if skill_id else None
    if skill_id and not skill:
        errors.append("Skill not found.")
    if skill and UserSkill.query.filter_by(user_id=current_user.id, skill_id=skill.id).first():
        errors.append("Skill already added to your profile.")
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        row = UserSkill(user_id=current_user.id, skill_id=skill.id, level=level)
        db.session.add(row)
        db.session.commit()
        return jsonify({"message": "Skill added.", "user_skill": row.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def update_my_skill(user_skill_id):
    row = db.session.get(UserSkill, user_skill_id)
    if not row or row.user_id != current_user.id:
        return jsonify({"error": "User skill not found."}), 404
    data = request.get_json(silent=True) or {}
    level = str(data.get("level") or "").strip().lower()
    if level not in SKILL_LEVELS:
        return jsonify({"errors": [f"level must be one of: {', '.join(SKILL_LEVELS)}."]}), 400
    try:
        row.level = level
        db.session.commit()
        return jsonify({"message": "User skill updated.", "user_skill": row.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def delete_my_skill(user_skill_id):
    row = db.session.get(UserSkill, user_skill_id)
    if not row or row.user_id != current_user.id:
        return jsonify({"error": "User skill not found."}), 404
    try:
        db.session.delete(row)
        db.session.commit()
        return jsonify({"message": "User skill deleted."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def verify_user_skill(user_skill_id):
    row = db.session.get(UserSkill, user_skill_id)
    if not row:
        return jsonify({"error": "User skill not found."}), 404

    job_ids = [j.id for j in Job.query.filter_by(posted_by=current_user.id).all()]
    if not job_ids:
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    related = Application.query.filter(
        Application.job_id.in_(job_ids),
        Application.seeker_id == row.user_id,
    ).first()
    if not related:
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    try:
        row.verified = True
        row.verified_by = current_user.id
        db.session.commit()
        return jsonify({"message": "Skill verified.", "user_skill": row.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def export_my_skills_csv():
    rows_data = UserSkill.query.filter_by(user_id=current_user.id).all()
    headers = ["skill_name", "category", "level"]
    rows = [
        [r.skill.name if r.skill else "", (r.skill.category if r.skill else "") or "", r.level]
        for r in rows_data
    ]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return rows_to_csv_response(f"my-skills-{today}.csv", headers, rows)


def import_my_skills_csv():
    file = request.files.get("file")
    rows, header_errors = parse_csv_file(file, ["skill_name", "category", "level"])
    if header_errors:
        return jsonify({"errors": header_errors}), 400

    created = skipped = 0
    errors = []
    try:
        for i, row in enumerate(rows, start=2):
            name = (row.get("skill_name") or "").strip()
            level = (row.get("level") or "beginner").strip().lower()
            category = (row.get("category") or "").strip() or None
            if not name:
                errors.append({"row": i, "message": "skill_name is required."})
                continue
            if level not in SKILL_LEVELS:
                errors.append({"row": i, "message": f"Invalid level: {level}"})
                continue
            skill = Skill.query.filter_by(name=name).first()
            if not skill:
                skill = Skill(name=name, category=category)
                db.session.add(skill)
                db.session.flush()
            if UserSkill.query.filter_by(user_id=current_user.id, skill_id=skill.id).first():
                skipped += 1
                continue
            db.session.add(UserSkill(user_id=current_user.id, skill_id=skill.id, level=level))
            created += 1
        db.session.commit()
        return jsonify({"created": created, "skipped": skipped, "errors": errors}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
