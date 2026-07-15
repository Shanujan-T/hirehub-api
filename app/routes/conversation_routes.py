from flask import Blueprint

from app.controllers import conversation_controller as ctrl
from app.middleware import jwt_required_active

conversations_bp = Blueprint("conversations", __name__, url_prefix="/api/conversations")
my_conversations_bp = Blueprint("my_conversations", __name__, url_prefix="/api/my")
messages_bp = Blueprint("messages", __name__, url_prefix="/api/messages")


@my_conversations_bp.route("/conversations", methods=["GET"])
@jwt_required_active
def get_my_conversations():
    return ctrl.get_my_conversations()


@conversations_bp.route("", methods=["POST"])
@jwt_required_active
def create_conversation():
    return ctrl.create_conversation()


@conversations_bp.route("/<int:conversation_id>/messages", methods=["GET"])
@jwt_required_active
def get_messages(conversation_id):
    return ctrl.get_messages(conversation_id)


@conversations_bp.route("/<int:conversation_id>/messages", methods=["POST"])
@jwt_required_active
def send_message(conversation_id):
    return ctrl.send_message(conversation_id)


@messages_bp.route("/<int:message_id>/read", methods=["PATCH"])
@jwt_required_active
def mark_read(message_id):
    return ctrl.mark_message_read(message_id)
