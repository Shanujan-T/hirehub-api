from flask import jsonify, request
from flask_jwt_extended import current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Conversation, Message, User


def _ordered_pair(a, b):
    return (a, b) if a < b else (b, a)


def _participant(conv):
    return current_user.id in (conv.participant_one_id, conv.participant_two_id)


def get_my_conversations():
    rows = Conversation.query.filter(
        or_(
            Conversation.participant_one_id == current_user.id,
            Conversation.participant_two_id == current_user.id,
        )
    ).order_by(Conversation.id.desc()).all()
    return jsonify({"conversations": [r.to_dict() for r in rows]}), 200


def create_conversation():
    data = request.get_json(silent=True)
    if not data or not data.get("user_id"):
        return jsonify({"errors": ["user_id is required."]}), 400
    other_id = int(data.get("user_id"))
    if other_id == current_user.id:
        return jsonify({"error": "Cannot start a conversation with yourself."}), 400
    if not db.session.get(User, other_id):
        return jsonify({"error": "User not found."}), 404

    p1, p2 = _ordered_pair(current_user.id, other_id)
    existing = Conversation.query.filter_by(participant_one_id=p1, participant_two_id=p2).first()
    if existing:
        return jsonify({"message": "Conversation already exists.", "conversation": existing.to_dict()}), 200

    try:
        conv = Conversation(participant_one_id=p1, participant_two_id=p2)
        db.session.add(conv)
        db.session.commit()
        return jsonify({"message": "Conversation created.", "conversation": conv.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def get_messages(conversation_id):
    conv = db.session.get(Conversation, conversation_id)
    if not conv:
        return jsonify({"error": "Conversation not found."}), 404
    if not _participant(conv):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    messages = Message.query.filter_by(conversation_id=conv.id).order_by(Message.id.asc()).all()
    return jsonify({"messages": [m.to_dict() for m in messages]}), 200


def send_message(conversation_id):
    conv = db.session.get(Conversation, conversation_id)
    if not conv:
        return jsonify({"error": "Conversation not found."}), 404
    if not _participant(conv):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    data = request.get_json(silent=True)
    if not data or not str(data.get("body") or "").strip():
        return jsonify({"errors": ["body is required."]}), 400
    try:
        msg = Message(
            conversation_id=conv.id,
            sender_id=current_user.id,
            body=str(data.get("body")).strip(),
        )
        db.session.add(msg)
        db.session.commit()
        return jsonify({"message": "Message sent.", "message_obj": msg.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def mark_message_read(message_id):
    msg = db.session.get(Message, message_id)
    if not msg:
        return jsonify({"error": "Message not found."}), 404
    conv = msg.conversation
    if not conv or not _participant(conv):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    if msg.sender_id == current_user.id:
        return jsonify({"error": "Sender cannot mark own message as read via this endpoint."}), 400
    try:
        msg.is_read = True
        db.session.commit()
        return jsonify({"message": "Message marked as read.", "message_obj": msg.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
