from flask import jsonify, request
from flask_jwt_extended import current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Application, Conversation, Message, User
from app.utils import utc_now
from app.utils.message_notifier import notify_new_message

MAX_MESSAGE_LENGTH = 2000


def _is_job_owner(application):
    job = application.job
    return job and current_user.role == "employer" and job.posted_by == current_user.id


def _can_access_application(application):
    if current_user.role == "admin":
        return True
    if application.seeker_id == current_user.id:
        return True
    return _is_job_owner(application)


def _participant(conv):
    return current_user.id in (conv.employer_id, conv.seeker_id)


def _unread_count(conversation_id, user_id):
    return (
        Message.query.filter_by(conversation_id=conversation_id)
        .filter(Message.sender_id != user_id, Message.read_at.is_(None))
        .count()
    )


def _last_message(conversation_id):
    return (
        Message.query.filter_by(conversation_id=conversation_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .first()
    )


def _serialize_list_item(conv):
    other = conv.seeker if current_user.id == conv.employer_id else conv.employer
    last = _last_message(conv.id)
    job_title = None
    if conv.application and conv.application.job:
        job_title = conv.application.job.title

    return {
        **conv.to_dict(include_application=True),
        "other_party": {
            "id": other.id,
            "full_name": other.full_name,
            "avatar_url": other.avatar_url,
            "role": other.role,
        }
        if other
        else None,
        "job_title": job_title,
        "last_message": last.to_dict() if last else None,
        "unread_count": _unread_count(conv.id, current_user.id),
    }


def create_or_get_application_conversation(application_id):
    application = db.session.get(Application, application_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404
    if not _can_access_application(application):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    job = application.job
    if not job:
        return jsonify({"error": "Job not found for this application."}), 404

    employer_id = job.posted_by
    seeker_id = application.seeker_id

    existing = Conversation.query.filter_by(application_id=application.id).first()
    if existing:
        return jsonify({
            "message": "Conversation already exists.",
            "conversation": _serialize_list_item(existing),
        }), 200

    try:
        conv = Conversation(
            application_id=application.id,
            employer_id=employer_id,
            seeker_id=seeker_id,
        )
        db.session.add(conv)
        db.session.commit()
        conv = db.session.get(Conversation, conv.id)
        return jsonify({
            "message": "Conversation created.",
            "conversation": _serialize_list_item(conv),
        }), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def list_conversations():
    rows = (
        Conversation.query.filter(
            or_(
                Conversation.employer_id == current_user.id,
                Conversation.seeker_id == current_user.id,
            )
        )
        .order_by(Conversation.id.desc())
        .all()
    )

    items = [_serialize_list_item(conv) for conv in rows]
    items.sort(
        key=lambda row: (
            row.get("last_message") or {}
        ).get("created_at")
        or row.get("created_at")
        or "",
        reverse=True,
    )
    return jsonify({"conversations": items}), 200


def get_messages(conversation_id):
    conv = db.session.get(Conversation, conversation_id)
    if not conv:
        return jsonify({"error": "Conversation not found."}), 404
    if not _participant(conv):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    messages = (
        Message.query.filter_by(conversation_id=conv.id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )
    return jsonify({
        "conversation": _serialize_list_item(conv),
        "messages": [m.to_dict() for m in messages],
    }), 200


def send_message(conversation_id):
    conv = db.session.get(Conversation, conversation_id)
    if not conv:
        return jsonify({"error": "Conversation not found."}), 404
    if not _participant(conv):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    data = request.get_json(silent=True)
    body = str(data.get("body") or "").strip() if data else ""
    if not body:
        return jsonify({"errors": ["body is required."]}), 400
    if len(body) > MAX_MESSAGE_LENGTH:
        return jsonify({"errors": [f"body must be at most {MAX_MESSAGE_LENGTH} characters."]}), 400

    recipient_id = conv.seeker_id if current_user.id == conv.employer_id else conv.employer_id
    recipient = db.session.get(User, recipient_id)

    try:
        msg = Message(
            conversation_id=conv.id,
            sender_id=current_user.id,
            body=body,
        )
        db.session.add(msg)
        if recipient:
            notify_new_message(recipient, current_user, conv, body)
        db.session.commit()
        return jsonify({"message": "Message sent.", "message_obj": msg.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def mark_conversation_read(conversation_id):
    conv = db.session.get(Conversation, conversation_id)
    if not conv:
        return jsonify({"error": "Conversation not found."}), 404
    if not _participant(conv):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    now = utc_now()
    try:
        (
            Message.query.filter_by(conversation_id=conv.id)
            .filter(Message.sender_id != current_user.id, Message.read_at.is_(None))
            .update({"read_at": now}, synchronize_session=False)
        )
        db.session.commit()
        return jsonify({"message": "Conversation marked as read."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def get_conversation_admin(conversation_id):
    conv = db.session.get(Conversation, conversation_id)
    if not conv:
        return jsonify({"error": "Conversation not found."}), 404

    messages = (
        Message.query.filter_by(conversation_id=conv.id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )
    return jsonify({
        "conversation": conv.to_dict(include_participants=True, include_application=True),
        "messages": [m.to_dict() for m in messages],
    }), 200
