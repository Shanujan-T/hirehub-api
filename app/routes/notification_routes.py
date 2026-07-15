from flask import Blueprint

from app.controllers import notification_controller as ctrl
from app.middleware import jwt_required_active

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api")
my_notifications_bp = Blueprint("my_notifications", __name__, url_prefix="/api/my")


@my_notifications_bp.route("/notifications", methods=["GET"])
@jwt_required_active
def get_my_notifications():
    return ctrl.get_my_notifications()


@my_notifications_bp.route("/notifications/read-all", methods=["PATCH"])
@jwt_required_active
def mark_all_read():
    return ctrl.mark_all_read()


@notifications_bp.route("/notifications/<int:notification_id>/read", methods=["PATCH"])
@jwt_required_active
def mark_read(notification_id):
    return ctrl.mark_notification_read(notification_id)
