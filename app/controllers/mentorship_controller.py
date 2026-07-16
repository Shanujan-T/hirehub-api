from datetime import datetime

from flask import jsonify, request
from flask_jwt_extended import current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Mentorship, MentorshipSession, MentorProfile, User
from app.models.mentor_profile_model import MENTORSHIP_FOCUS_AREAS
from app.models.mentorship_session_model import SESSION_STATUSES
from app.utils.social_helpers import notify


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

    profile = MentorProfile.query.filter_by(user_id=mentor.id).first()
    if profile and not profile.is_available:
        return jsonify({"error": "Mentor is not currently available."}), 400

    focus_area = data.get("focus_area")
    if focus_area and focus_area not in MENTORSHIP_FOCUS_AREAS:
        return jsonify({"errors": [f"focus_area must be one of: {', '.join(MENTORSHIP_FOCUS_AREAS)}."]}), 400

    if Mentorship.query.filter_by(mentor_id=mentor.id, mentee_id=current_user.id).first():
        return jsonify({"error": "Mentorship request already exists."}), 400

    active_count = Mentorship.query.filter_by(mentor_id=mentor.id, status="active").count()
    if profile and active_count >= profile.max_mentees:
        return jsonify({"error": "Mentor has reached maximum mentee capacity."}), 400

    try:
        row = Mentorship(
            mentor_id=mentor.id,
            mentee_id=current_user.id,
            community_id=data.get("community_id"),
            focus_area=focus_area,
            message=data.get("message"),
            status="requested",
        )
        db.session.add(row)
        db.session.flush()
        notify(
            mentor.id,
            "mentorship_request",
            f"{current_user.full_name} requested mentorship.",
            f"/mentorships/{row.id}",
        )
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
    return jsonify({"mentorships": [r.to_dict(include_sessions=True) for r in rows]}), 200


def discover_mentors():
    focus_area = (request.args.get("focus_area") or "").strip().lower()
    community_id = request.args.get("community_id")
    q = (request.args.get("q") or "").strip()

    query = MentorProfile.query.filter_by(is_available=True)
    if community_id:
        query = query.filter(
            or_(
                MentorProfile.community_id == int(community_id),
                MentorProfile.community_id.is_(None),
            )
        )
    profiles = query.order_by(MentorProfile.id.desc()).all()

    results = []
    for profile in profiles:
        if focus_area and focus_area not in profile._parse_json_list(profile.available_for):
            continue
        if q and q.lower() not in (profile.user.full_name or "").lower():
            if q.lower() not in (profile.headline or "").lower():
                continue
        active_count = Mentorship.query.filter_by(
            mentor_id=profile.user_id, status="active"
        ).count()
        data = profile.to_dict()
        data["active_mentees"] = active_count
        data["has_capacity"] = active_count < profile.max_mentees
        results.append(data)

    return jsonify({"mentors": results}), 200


def get_mentor_profile(user_id):
    profile = MentorProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return jsonify({"error": "Mentor profile not found."}), 404
    return jsonify({"mentor_profile": profile.to_dict()}), 200


def upsert_mentor_profile():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    profile = MentorProfile.query.filter_by(user_id=current_user.id).first()
    try:
        if not profile:
            profile = MentorProfile(user_id=current_user.id)
            db.session.add(profile)

        for field in ("headline", "bio", "years_experience", "community_id", "max_mentees"):
            if field in data:
                setattr(profile, field, data.get(field))
        if "expertise_areas" in data:
            profile.set_list_field("expertise_areas", data.get("expertise_areas"))
        if "available_for" in data:
            available = data.get("available_for") or []
            invalid = [a for a in available if a not in MENTORSHIP_FOCUS_AREAS]
            if invalid:
                return jsonify({"errors": [f"Invalid focus areas: {', '.join(invalid)}"]}), 400
            profile.set_list_field("available_for", available)
        if "is_available" in data:
            profile.is_available = bool(data.get("is_available"))

        db.session.commit()
        return jsonify({"message": "Mentor profile saved.", "mentor_profile": profile.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


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
        notify(
            row.mentee_id,
            "mentorship_accepted",
            f"{current_user.full_name} accepted your mentorship request.",
            f"/mentorships/{row.id}",
        )
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
        notify(
            row.mentee_id,
            "mentorship_declined",
            f"{current_user.full_name} declined your mentorship request.",
            f"/mentorships/{row.id}",
        )
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
        other_id = row.mentee_id if current_user.id == row.mentor_id else row.mentor_id
        notify(other_id, "mentorship_ended", "A mentorship has ended.", f"/mentorships/{row.id}")
        db.session.commit()
        return jsonify({"message": "Mentorship ended.", "mentorship": row.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def create_session(mentorship_id):
    row = db.session.get(Mentorship, mentorship_id)
    if not row:
        return jsonify({"error": "Mentorship not found."}), 404
    if current_user.id not in (row.mentor_id, row.mentee_id):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    if row.status != "active":
        return jsonify({"error": "Sessions can only be created for active mentorships."}), 400

    data = request.get_json(silent=True) or {}
    topic = str(data.get("topic") or "").strip()
    if not topic:
        return jsonify({"errors": ["topic is required."]}), 400

    focus_area = data.get("focus_area")
    if focus_area and focus_area not in MENTORSHIP_FOCUS_AREAS:
        return jsonify({"errors": [f"focus_area must be one of: {', '.join(MENTORSHIP_FOCUS_AREAS)}."]}), 400

    scheduled_at = None
    if data.get("scheduled_at"):
        try:
            scheduled_at = datetime.fromisoformat(str(data.get("scheduled_at")))
        except ValueError:
            return jsonify({"errors": ["scheduled_at must be ISO format."]}), 400

    try:
        session = MentorshipSession(
            mentorship_id=row.id,
            topic=topic,
            focus_area=focus_area,
            scheduled_at=scheduled_at,
            notes=data.get("notes"),
            status="scheduled",
        )
        db.session.add(session)
        other_id = row.mentee_id if current_user.id == row.mentor_id else row.mentor_id
        notify(
            other_id,
            "mentorship_session",
            f"New mentorship session scheduled: {topic}",
            f"/mentorships/{row.id}",
        )
        db.session.commit()
        return jsonify({"message": "Session created.", "session": session.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def update_session(mentorship_id, session_id):
    row = db.session.get(Mentorship, mentorship_id)
    session = db.session.get(MentorshipSession, session_id)
    if not row or not session or session.mentorship_id != row.id:
        return jsonify({"error": "Session not found."}), 404
    if current_user.id not in (row.mentor_id, row.mentee_id):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    data = request.get_json(silent=True) or {}
    try:
        if "topic" in data:
            session.topic = str(data.get("topic") or "").strip()
        if "notes" in data:
            session.notes = data.get("notes")
        if "focus_area" in data:
            session.focus_area = data.get("focus_area")
        if "status" in data:
            status = str(data.get("status")).strip().lower()
            if status not in SESSION_STATUSES:
                return jsonify({"errors": [f"status must be one of: {', '.join(SESSION_STATUSES)}."]}), 400
            session.status = status
        if "scheduled_at" in data and data.get("scheduled_at"):
            session.scheduled_at = datetime.fromisoformat(str(data.get("scheduled_at")))
        db.session.commit()
        return jsonify({"message": "Session updated.", "session": session.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
