from datetime import datetime

from flask import jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Application, Job, Notification
from app.utils.csv_utils import rows_to_csv_response
from app.utils.pdf_utils import document_pdf_response


def _notify(user_id, type_, message, link_url=None):
    db.session.add(
        Notification(user_id=user_id, type=type_, message=message, link_url=link_url)
    )


def _is_job_owner(application):
    job = application.job
    return job and current_user.role == "employer" and job.posted_by == current_user.id


def _can_view_application(application):
    if current_user.role == "admin":
        return True
    if application.seeker_id == current_user.id:
        return True
    return _is_job_owner(application)


def create_application():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    job_id = data.get("job_id")
    if not job_id:
        return jsonify({"errors": ["job_id is required."]}), 400

    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    if job.status != "open":
        return jsonify({"error": "Job is not open for applications."}), 400
    if Application.query.filter_by(job_id=job.id, seeker_id=current_user.id).first():
        return jsonify({"error": "You have already applied to this job."}), 400

    resume = data.get("resume_url") or current_user.resume_url
    try:
        app_row = Application(
            job_id=job.id,
            seeker_id=current_user.id,
            cover_letter=data.get("cover_letter"),
            resume_url=str(resume).strip() if resume else None,
            status="pending",
        )
        db.session.add(app_row)
        db.session.commit()
        return jsonify({"message": "Application submitted.", "application": app_row.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def get_my_applications():
    apps = (
        Application.query.filter_by(seeker_id=current_user.id)
        .order_by(Application.id.desc())
        .all()
    )
    return jsonify({"applications": [a.to_dict() for a in apps]}), 200


def get_applications():
    apps = Application.query.order_by(Application.id.desc()).all()
    return jsonify({"applications": [a.to_dict() for a in apps]}), 200


def get_application(application_id):
    app_row = db.session.get(Application, application_id)
    if not app_row:
        return jsonify({"error": "Application not found."}), 404
    if not _can_view_application(app_row):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    return jsonify({"application": app_row.to_dict()}), 200


def _set_status(application_id, new_status, employer_only=True, seeker_only=False):
    app_row = db.session.get(Application, application_id)
    if not app_row:
        return jsonify({"error": "Application not found."}), 404

    if employer_only and not _is_job_owner(app_row):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    if seeker_only and app_row.seeker_id != current_user.id:
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    try:
        app_row.status = new_status
        _notify(
            app_row.seeker_id,
            "application_status",
            f"Your application status changed to {new_status}.",
            link_url=f"/applications/{app_row.id}",
        )
        db.session.commit()
        return jsonify({"message": f"Application {new_status}.", "application": app_row.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def shortlist_application(application_id):
    return _set_status(application_id, "shortlisted", employer_only=True)


def accept_application(application_id):
    return _set_status(application_id, "accepted", employer_only=True)


def reject_application(application_id):
    return _set_status(application_id, "rejected", employer_only=True)


def withdraw_application(application_id):
    return _set_status(application_id, "withdrawn", employer_only=False, seeker_only=True)


def delete_application(application_id):
    app_row = db.session.get(Application, application_id)
    if not app_row:
        return jsonify({"error": "Application not found."}), 404
    try:
        db.session.delete(app_row)
        db.session.commit()
        return jsonify({"message": "Application deleted."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def export_application_pdf(application_id):
    app_row = db.session.get(Application, application_id)
    if not app_row:
        return jsonify({"error": "Application not found."}), 404
    if not _can_view_application(app_row):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    job = app_row.job
    seeker = app_row.seeker
    company = job.company.name if job and job.company else "—"
    sections = [
        ("Candidate", seeker.full_name if seeker else "—"),
        ("Job", job.title if job else "—"),
        ("Company", company),
        ("Status", app_row.status),
        ("Applied", app_row.created_at.isoformat() if app_row.created_at else "—"),
        ("Resume", app_row.resume_url or "—"),
        ("Cover letter", app_row.cover_letter or "—"),
    ]
    return document_pdf_response(
        f"application-{app_row.id}.pdf",
        "Application Summary",
        sections,
    )


def export_applications_csv():
    if current_user.role == "admin":
        apps = Application.query.order_by(Application.id).all()
    elif current_user.role == "seeker":
        apps = Application.query.filter_by(seeker_id=current_user.id).all()
    else:
        job_ids = [j.id for j in Job.query.filter_by(posted_by=current_user.id).all()]
        apps = Application.query.filter(Application.job_id.in_(job_ids)).all() if job_ids else []

    headers = ["id", "job_id", "seeker_id", "status", "created_at"]
    rows = [
        [a.id, a.job_id, a.seeker_id, a.status, a.created_at.isoformat() if a.created_at else ""]
        for a in apps
    ]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return rows_to_csv_response(f"applications-{today}.csv", headers, rows)
