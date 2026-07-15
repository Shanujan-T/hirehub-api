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
