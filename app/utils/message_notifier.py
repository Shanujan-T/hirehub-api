"""Notify recipients about new application-scoped messages (in-app + optional WhatsApp)."""

from datetime import timedelta

from app.extensions import db
from app.models import Notification
from app.services.whatsapp_notifier import send_whatsapp_message
from app.utils import utc_now


def _should_notify_in_app(notify_via: str | None) -> bool:
    channel = (notify_via or "email").strip().lower()
    return channel in ("email", "both")


def _should_notify_whatsapp(notify_via: str | None) -> bool:
    channel = (notify_via or "email").strip().lower()
    return channel in ("whatsapp", "both")


def _recipient_recently_active(recipient) -> bool:
    if not recipient.last_active_at:
        return False
    return recipient.last_active_at >= utc_now() - timedelta(minutes=10)


def notify_new_message(recipient, sender, conversation, message_preview: str):
    """Send notification only when recipient has been inactive for 10+ minutes."""
    if _recipient_recently_active(recipient):
        return

    job_title = "your application"
    if conversation.application and conversation.application.job:
        job_title = conversation.application.job.title

    text = f"New message from {sender.full_name} about {job_title}"
    link_url = f"/messages/{conversation.id}"
    notify_via = (recipient.notify_via or "email").strip().lower()

    if notify_via == "none":
        return

    if _should_notify_in_app(notify_via):
        db.session.add(
            Notification(
                user_id=recipient.id,
                type="message",
                message=text,
                link_url=link_url,
            )
        )

    if _should_notify_whatsapp(notify_via):
        number = recipient.whatsapp_number or recipient.phone
        if number:
            preview = message_preview[:120] + ("…" if len(message_preview) > 120 else "")
            send_whatsapp_message(number, f"{text}\n\"{preview}\"\nView: {link_url}")
