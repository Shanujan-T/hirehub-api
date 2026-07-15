import re
from datetime import datetime

from flask import jsonify, request
from flask_jwt_extended import current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import User
from app.models.user_model import EDUCATION_LEVELS, PUBLIC_REGISTER_ROLES
from app.utils.csv_utils import parse_csv_file, rows_to_csv_response


def _safe_role_for_write(role, default="seeker"):
    """Never allow assigning admin via API — only seeker|employer."""
    if role is None or str(role).strip() == "":
        return default
    r = str(role).strip().lower()
    if r in ("jobseeker", "job_seeker"):
        r = "seeker"
    if r not in PUBLIC_REGISTER_ROLES:
        return None
    return r


def get_users():
    q = (request.args.get("q") or "").strip().lower()
    role = (request.args.get("role") or "").strip().lower()
    location = (request.args.get("location") or "").strip().lower()

    query = User.query
    if q:
        query = query.filter(or_(User.email.ilike(f"%{q}%"), User.full_name.ilike(f"%{q}%")))
    if role:
        query = query.filter(User.role == role)
    if location:
        query = query.filter(User.location.ilike(f"%{location}%"))

    users = query.order_by(User.id.desc()).all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    if current_user.role != "admin" and current_user.id != user.id:
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    return jsonify({"user": user.to_dict(include_skills=True)}), 200
