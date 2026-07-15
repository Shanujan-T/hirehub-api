from flask import jsonify, request
from flask_jwt_extended import current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Mentorship, User


def create_mentorship():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400
    mentor_id = data.get("mentor_id")
    if not mentor_id:
        return jsonify({"errors": ["mentor_id is required."]}), 400
    if int(mentor_id) == current_user.id:
        return jsonify({"error": "Cannot request mentorship from yourself."}), 400
    mentor = db.session.get(User, mentor_id)
    if not mentor:
        return jsonify({"error": "Mentor not found."}), 404
    if Mentorship.query.filter_by(mentor_id=mentor.id, mentee_id=current_user.id).first():
        return jsonify({"error": "Mentorship request already exists."}), 400
    try:
        row = Mentorship(
            mentor_id=mentor.id,
            mentee_id=current_user.id,
            message=data.get("message"),
            status="requested",
        )
        db.session.add(row)
        db.session.commit()
        return jsonify({"message": "Mentorship requested.", "mentorship": row.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def get_my_mentorships():
    rows = Mentorship.query.filter(
        or_(
            Mentorship.mentor_id == current_user.id,
            Mentorship.mentee_id == current_user.id,
        )
    ).order_by(Mentorship.id.desc()).all()
    return jsonify({"mentorships": [r.to_dict() for r in rows]}), 200


def _get_owned_as_mentor(mentorship_id):
    row = db.session.get(Mentorship, mentorship_id)
    if not row:
        return None, (jsonify({"error": "Mentorship not found."}), 404)
    if row.mentor_id != current_user.id:
        return None, (jsonify({"error": "Access forbidden: insufficient permissions."}), 403)
    return row, None


def accept_mentorship(mentorship_id):
    row, err = _get_owned_as_mentor(mentorship_id)
    if err:
        return err
    try:
        row.status = "active"
        db.session.commit()
        return jsonify({"message": "Mentorship accepted.", "mentorship": row.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def decline_mentorship(mentorship_id):
    row, err = _get_owned_as_mentor(mentorship_id)
    if err:
        return err
    try:
        row.status = "declined"
        db.session.commit()
        return jsonify({"message": "Mentorship declined.", "mentorship": row.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def end_mentorship(mentorship_id):
    row = db.session.get(Mentorship, mentorship_id)
    if not row:
        return jsonify({"error": "Mentorship not found."}), 404
    if current_user.id not in (row.mentor_id, row.mentee_id):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    try:
        row.status = "ended"
        db.session.commit()
        return jsonify({"message": "Mentorship ended.", "mentorship": row.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
