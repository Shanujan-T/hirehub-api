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
