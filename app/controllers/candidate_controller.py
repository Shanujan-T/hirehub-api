from flask import jsonify, request
from sqlalchemy import or_

from app.extensions import db
from app.models import Skill, User, UserSkill
from app.utils.pdf_utils import document_pdf_response


def get_candidates():
    q = (request.args.get("q") or "").strip().lower()
    location = (request.args.get("location") or "").strip().lower()
    skill = (request.args.get("skill") or "").strip().lower()
    education_level = (request.args.get("education_level") or "").strip().lower()

    query = User.query.filter(User.role == "seeker", User.is_active.is_(True))
    if q:
        query = query.filter(
            or_(User.full_name.ilike(f"%{q}%"), User.bio.ilike(f"%{q}%"), User.email.ilike(f"%{q}%"))
        )
    if location:
        query = query.filter(User.location.ilike(f"%{location}%"))
    if education_level:
        query = query.filter(User.education_level == education_level)
    if skill:
        query = (
            query.join(UserSkill)
            .join(Skill)
            .filter(Skill.name.ilike(f"%{skill}%"))
            .distinct()
        )

    candidates = query.order_by(User.id.desc()).all()
    return jsonify({"candidates": [c.to_dict(include_skills=True) for c in candidates]}), 200


def get_candidate(candidate_id):
    user = db.session.get(User, candidate_id)
    if not user or user.role != "seeker":
        return jsonify({"error": "Candidate not found."}), 404
    return jsonify({"candidate": user.to_dict(include_skills=True)}), 200


def export_candidate_pdf(candidate_id):
    user = db.session.get(User, candidate_id)
    if not user or user.role != "seeker":
        return jsonify({"error": "Candidate not found."}), 404

    skills_text = ", ".join(
        f"{us.skill.name} ({us.level})" for us in user.skills if us.skill
    ) or "None"

    sections = [
        ("Name", user.full_name),
        ("Email", user.email),
        ("Location", user.location or "—"),
        ("Education", user.education_level or "—"),
        ("Bio", user.bio or "—"),
        ("Resume", user.resume_url or "—"),
        ("Skills", skills_text),
    ]
    return document_pdf_response(
        f"candidate-{user.id}.pdf",
        f"Candidate Profile — {user.full_name}",
        sections,
    )
