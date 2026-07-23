from flask import Blueprint

from app.controllers import conversation_controller as ctrl
from app.middleware import jwt_required_active, require_role

conversations_bp = Blueprint("conversations", __name__, url_prefix="/api/conversations")
my_conversations_bp = Blueprint("my_conversations", __name__, url_prefix="/api/my")


@conversations_bp.route("", methods=["GET"])
@jwt_required_active
def list_conversations():
    return ctrl.list_conversations()


@my_conversations_bp.route("/conversations", methods=["GET"])
@jwt_required_active
def list_my_conversations():
    return ctrl.list_conversations()


@conversations_bp.route("/<int:conversation_id>/messages", methods=["GET"])
@jwt_required_active
def get_messages(conversation_id):
    return ctrl.get_messages(conversation_id)


@conversations_bp.route("/<int:conversation_id>/messages", methods=["POST"])
@jwt_required_active
def send_message(conversation_id):
    return ctrl.send_message(conversation_id)


@conversations_bp.route("/<int:conversation_id>/read", methods=["PATCH"])
@jwt_required_active
def mark_conversation_read(conversation_id):
    return ctrl.mark_conversation_read(conversation_id)


@conversations_bp.route("/<int:conversation_id>", methods=["GET"])
@require_role("admin")
def get_conversation_admin(conversation_id):
    return ctrl.get_conversation_admin(conversation_id)
