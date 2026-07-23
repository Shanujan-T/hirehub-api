from datetime import datetime

from flask import jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Application, Interview, Notification
from app.controllers.application_controller import (
    _can_view_application,
    _is_job_owner,
    _log_status_change,
    _notify,
)


def _active_interview(application_id):
    return (
        Interview.query.filter_by(application_id=application_id)
        .filter(Interview.status.in_(("proposed", "confirmed")))
        .order_by(Interview.id.desc())
        .first()
    )


def _parse_slot(value):
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def propose_interview(application_id):
    app_row = db.session.get(Application, application_id)
    if not app_row:
        return jsonify({"error": "Application not found."}), 404
    if not _is_job_owner(app_row):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    if app_row.status != "shortlisted":
        return jsonify({"errors": ["Interview can only be proposed for shortlisted applications."]}), 400
    if _active_interview(application_id):
        return jsonify({"error": "An active interview already exists for this application."}), 400

    data = request.get_json(silent=True) or {}
    raw_slots = data.get("slots")
    if not isinstance(raw_slots, list):
        return jsonify({"errors": ["slots must be an array of 2-4 ISO datetime strings."]}), 400
    if len(raw_slots) < 2 or len(raw_slots) > 4:
        return jsonify({"errors": ["Provide between 2 and 4 time slots."]}), 400

    parsed_slots = []
    for slot in raw_slots:
        dt = _parse_slot(slot)
        if not dt:
            return jsonify({"errors": [f"Invalid datetime slot: {slot}"]}), 400
        parsed_slots.append(dt.isoformat())

    try:
        interview = Interview(
            application_id=application_id,
            proposed_by=current_user.id,
            slots=parsed_slots,
            status="proposed",
        )
        db.session.add(interview)
        db.session.flush()
        _log_status_change(application_id, app_row.status, "interview_proposed", current_user.id)
        _notify(
            app_row.seeker_id,
            "application_status",
            "An employer proposed interview time slots for your application.",
            link_url=f"/applications/{application_id}",
        )
        db.session.commit()
        return jsonify({
            "message": "Interview slots proposed.",
            "interview": interview.to_dict(),
        }), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def get_application_interview(application_id):
    app_row = db.session.get(Application, application_id)
    if not app_row:
        return jsonify({"error": "Application not found."}), 404
    if not _can_view_application(app_row):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    interview = _active_interview(application_id)
    if not interview:
        latest = (
            Interview.query.filter_by(application_id=application_id)
            .order_by(Interview.id.desc())
            .first()
        )
        if latest and latest.status == "cancelled":
            return jsonify({"interview": latest.to_dict()}), 200
        return jsonify({"interview": None}), 200
    return jsonify({"interview": interview.to_dict()}), 200


def select_interview_slot(interview_id):
    interview = db.session.get(Interview, interview_id)
    if not interview:
        return jsonify({"error": "Interview not found."}), 404

    app_row = interview.application
    if app_row.seeker_id != current_user.id:
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    if interview.status != "proposed":
        return jsonify({"error": "Interview is not awaiting candidate selection."}), 400

    data = request.get_json(silent=True) or {}
    selected = data.get("selected_slot")
    if not selected:
        return jsonify({"errors": ["selected_slot is required."]}), 400

    selected_dt = _parse_slot(selected)
    if not selected_dt:
        return jsonify({"errors": ["selected_slot must be a valid ISO datetime."]}), 400

    valid_slot = False
    for slot in interview.slots or []:
        slot_dt = _parse_slot(slot)
        if slot_dt and slot_dt == selected_dt:
            valid_slot = True
            break
    if not valid_slot:
        return jsonify({"errors": ["selected_slot must be one of the proposed slots."]}), 400

    try:
        interview.selected_slot = selected_dt
        interview.status = "confirmed"
        _log_status_change(app_row.id, app_row.status, "interview_confirmed", current_user.id)
        if app_row.job and app_row.job.posted_by:
            _notify(
                app_row.job.posted_by,
                "application_status",
                f"Interview confirmed for {app_row.job.title}.",
                link_url=f"/employer/jobs/{app_row.job_id}/applicants",
            )
        db.session.commit()
        return jsonify({
            "message": "Interview slot confirmed.",
            "interview": interview.to_dict(),
        }), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def cancel_interview(interview_id):
    interview = db.session.get(Interview, interview_id)
    if not interview:
        return jsonify({"error": "Interview not found."}), 404

    app_row = interview.application
    if not _can_view_application(app_row):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    if interview.status == "cancelled":
        return jsonify({"message": "Interview already cancelled.", "interview": interview.to_dict()}), 200

    try:
        interview.status = "cancelled"
        _log_status_change(app_row.id, app_row.status, "interview_cancelled", current_user.id)
        other_id = (
            app_row.seeker_id
            if current_user.id != app_row.seeker_id
            else (app_row.job.posted_by if app_row.job else None)
        )
        if other_id:
            _notify(
                other_id,
                "application_status",
                "An interview was cancelled.",
                link_url=f"/applications/{app_row.id}",
            )
        db.session.commit()
        return jsonify({
            "message": "Interview cancelled.",
            "interview": interview.to_dict(),
        }), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
