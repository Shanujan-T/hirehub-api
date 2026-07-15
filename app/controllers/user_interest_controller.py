from flask import jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Interest, UserInterest


def get_my_interests():
    rows = UserInterest.query.filter_by(user_id=current_user.id).order_by(UserInterest.id.desc()).all()
    return jsonify({"user_interests": [r.to_dict() for r in rows]}), 200


def create_my_interest():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400
    interest_id = data.get("interest_id")
    if not interest_id:
        return jsonify({"errors": ["interest_id is required."]}), 400
    interest = db.session.get(Interest, interest_id)
    if not interest:
        return jsonify({"error": "Interest not found."}), 404
    if UserInterest.query.filter_by(user_id=current_user.id, interest_id=interest.id).first():
        return jsonify({"error": "Interest already attached."}), 400
    try:
        row = UserInterest(user_id=current_user.id, interest_id=interest.id)
        db.session.add(row)
        db.session.commit()
        return jsonify({"message": "Interest attached.", "user_interest": row.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def delete_my_interest(user_interest_id):
    row = db.session.get(UserInterest, user_interest_id)
    if not row or row.user_id != current_user.id:
        return jsonify({"error": "User interest not found."}), 404
    try:
        db.session.delete(row)
        db.session.commit()
        return jsonify({"message": "User interest deleted."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
