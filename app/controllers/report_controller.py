from flask import jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Conversation, Message, Report
from app.models.report_model import REPORT_STATUSES, REPORT_TARGET_TYPES


def create_report():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    errors = []
    target_type = str(data.get("target_type") or "").strip().lower()
    target_id = data.get("target_id")
    reason = str(data.get("reason") or "").strip()

    if target_type not in REPORT_TARGET_TYPES:
        errors.append(f"target_type must be one of: {', '.join(REPORT_TARGET_TYPES)}.")
    if not target_id:
        errors.append("target_id is required.")
    if not reason:
        errors.append("reason is required.")
    if errors:
        return jsonify({"errors": errors}), 400

    target_id_int = int(target_id)
    if target_type == "conversation":
        conv = db.session.get(Conversation, target_id_int)
        if not conv:
            return jsonify({"error": "Conversation not found."}), 404
        if current_user.id not in (conv.employer_id, conv.seeker_id):
            return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    elif target_type == "message":
        msg = db.session.get(Message, target_id_int)
        if not msg or not msg.conversation:
            return jsonify({"error": "Message not found."}), 404
        conv = msg.conversation
        if current_user.id not in (conv.employer_id, conv.seeker_id):
            return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    try:
        report = Report(
            reporter_id=current_user.id,
            target_type=target_type,
            target_id=target_id_int,
            reason=reason,
            details=data.get("details"),
            status="open",
        )
        db.session.add(report)
        db.session.commit()
        return jsonify({"message": "Report filed.", "report": report.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def get_reports():
    status = (request.args.get("status") or "").strip().lower()
    target_type = (request.args.get("target_type") or "").strip().lower()
    query = Report.query
    if status:
        query = query.filter(Report.status == status)
    if target_type:
        query = query.filter(Report.target_type == target_type)
    reports = query.order_by(Report.id.desc()).all()
    return jsonify({"reports": [r.to_dict() for r in reports]}), 200


def get_report(report_id):
    report = db.session.get(Report, report_id)
    if not report:
        return jsonify({"error": "Report not found."}), 404

    payload = {"report": report.to_dict()}
    if report.target_type == "conversation":
        conv = db.session.get(Conversation, report.target_id)
        if conv:
            messages = (
                Message.query.filter_by(conversation_id=conv.id)
                .order_by(Message.created_at.asc(), Message.id.asc())
                .all()
            )
            payload["conversation"] = conv.to_dict(
                include_participants=True,
                include_application=True,
            )
            payload["messages"] = [m.to_dict() for m in messages]
    elif report.target_type == "message":
        msg = db.session.get(Message, report.target_id)
        if msg and msg.conversation:
            conv = msg.conversation
            messages = (
                Message.query.filter_by(conversation_id=conv.id)
                .order_by(Message.created_at.asc(), Message.id.asc())
                .all()
            )
            payload["reported_message"] = msg.to_dict()
            payload["conversation"] = conv.to_dict(
                include_participants=True,
                include_application=True,
            )
            payload["messages"] = [m.to_dict() for m in messages]

    return jsonify(payload), 200


def resolve_report(report_id):
    report = db.session.get(Report, report_id)
    if not report:
        return jsonify({"error": "Report not found."}), 404

    data = request.get_json(silent=True) or {}
    status = str(data.get("status") or "").strip().lower()
    if status not in ("reviewed", "dismissed", "actioned"):
        return jsonify({"errors": ["status must be reviewed, dismissed, or actioned."]}), 400

    try:
        report.status = status
        report.resolved_by = current_user.id
        db.session.commit()
        return jsonify({"message": "Report resolved.", "report": report.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
