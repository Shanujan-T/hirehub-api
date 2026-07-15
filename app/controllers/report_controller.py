from flask import jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Report
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

    try:
        report = Report(
            reporter_id=current_user.id,
            target_type=target_type,
            target_id=int(target_id),
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
    return jsonify({"report": report.to_dict()}), 200


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
