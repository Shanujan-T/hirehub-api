"""Synchronous job-alert notifications (in-app + optional WhatsApp)."""

from app.extensions import db
from app.models import Notification, User
from app.services.whatsapp_notifier import send_whatsapp_message
from app.utils.job_alert_utils import find_matching_saved_searches


def _job_alert_message(job) -> str:
    company_name = job.company.name if job.company else "a company"
    location = f" ({job.location})" if job.location else ""
    return f"New job match: {job.title} at {company_name}{location}"


def find_skill_matching_seekers(job):
    """Seekers whose skills overlap with the job's required skills."""
    job_skill_ids = {js.skill_id for js in job.job_skills}
    if not job_skill_ids:
        return []

    matches = []
    for seeker in User.query.filter_by(role="seeker", is_active=True).all():
        user_skill_ids = {us.skill_id for us in seeker.skills}
        if user_skill_ids & job_skill_ids:
            matches.append(seeker)
    return matches


def _should_notify_in_app(notify_via: str | None) -> bool:
    channel = (notify_via or "email").strip().lower()
    return channel in ("email", "both")


def _should_notify_whatsapp(notify_via: str | None) -> bool:
    channel = (notify_via or "email").strip().lower()
    return channel in ("whatsapp", "both")


def _send_job_alert(user, job):
    message = _job_alert_message(job)
    link_url = f"/jobs/{job.id}"
    notify_via = (user.notify_via or "email").strip().lower()

    if notify_via == "none":
        return

    if _should_notify_in_app(notify_via):
        db.session.add(
            Notification(
                user_id=user.id,
                type="job_alert",
                message=message,
                link_url=link_url,
            )
        )

    if _should_notify_whatsapp(notify_via):
        number = user.whatsapp_number or user.phone
        if number:
            send_whatsapp_message(number, f"{message}\nView: {link_url}")


def notify_job_created(job):
    """Notify seekers via saved-search match and skill overlap (best-effort)."""
    notified_ids: set[int] = set()

    for search in find_matching_saved_searches(job):
        user = search.user
        if user and user.id not in notified_ids:
            _send_job_alert(user, job)
            notified_ids.add(user.id)

    for seeker in find_skill_matching_seekers(job):
        if seeker.id not in notified_ids:
            _send_job_alert(seeker, job)
            notified_ids.add(seeker.id)

    if notified_ids:
        db.session.commit()
