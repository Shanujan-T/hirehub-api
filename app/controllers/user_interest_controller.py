from flask import jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Interest, UserInterest


def get_my_interests():
    rows = UserInterest.query.filter_by(user_id=current_user.id).order_by(UserInterest.id.desc()).all()
    return jsonify({"user_interests": [r.to_dict() for r in rows]}), 200
