from flask import jsonify
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Notification


def get_my_notifications():
    rows = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.id.desc())
        .all()
    )
    return jsonify({"notifications": [n.to_dict() for n in rows]}), 200


def mark_notification_read(notification_id):
    row = db.session.get(Notification, notification_id)
    if not row or row.user_id != current_user.id:
        return jsonify({"error": "Notification not found."}), 404
    try:
        row.is_read = True
        db.session.commit()
        return jsonify({"message": "Notification marked as read.", "notification": row.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def mark_all_read():
    try:
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update(
            {"is_read": True}
        )
        db.session.commit()
        return jsonify({"message": "All notifications marked as read."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
