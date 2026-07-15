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


def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    is_admin = current_user.role == "admin"
    is_owner = current_user.id == user.id
    if not is_admin and not is_owner:
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    errors = []

    # Role: never elevate to admin. Owner cannot change role. Admin → seeker|employer only.
    if "role" in data:
        if not is_admin:
            errors.append("role cannot be changed.")
        else:
            new_role = _safe_role_for_write(data.get("role"), default=None)
            if new_role is None:
                errors.append("role must be 'seeker' or 'employer'. Cannot assign admin via API.")
            else:
                user.role = new_role

    if "full_name" in data:
        name = str(data.get("full_name") or "").strip()
        if not name:
            errors.append("full_name cannot be empty.")
        else:
            user.full_name = name

    for field in ("bio", "location", "phone", "resume_url", "avatar_url"):
        if field in data:
            val = data.get(field)
            setattr(user, field, str(val).strip() if val not in (None, "") else None)

    if "education_level" in data:
        level = data.get("education_level")
        if level in (None, ""):
            user.education_level = None
        else:
            level = str(level).strip().lower()
            if level not in EDUCATION_LEVELS:
                errors.append(f"education_level must be one of: {', '.join(EDUCATION_LEVELS)}.")
            else:
                user.education_level = level

    if "password" in data and data.get("password"):
        if len(str(data.get("password"))) < 6:
            errors.append("password must be at least 6 characters long.")
        else:
            user.set_password(str(data.get("password")))

    if "is_active" in data and is_admin:
        user.is_active = bool(data.get("is_active"))

    if errors:
        return jsonify({"errors": errors}), 400

    try:
        db.session.commit()
        return jsonify({"message": "User updated successfully.", "user": user.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def patch_user_status(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    if user.id == current_user.id:
        return jsonify({"error": "Cannot change your own status."}), 400

    data = request.get_json(silent=True) or {}
    if "is_active" not in data:
        return jsonify({"errors": ["is_active is required."]}), 400

    try:
        user.is_active = bool(data.get("is_active"))
        db.session.commit()
        return jsonify({"message": "User status updated.", "user": user.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    if user.id == current_user.id:
        return jsonify({"error": "Cannot delete your own account via this endpoint."}), 400

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def export_users_csv():
    users = User.query.order_by(User.id).all()
    headers = ["email", "full_name", "role", "location", "education_level", "is_active"]
    rows = [
        [u.email, u.full_name, u.role, u.location or "", u.education_level or "", u.is_active]
        for u in users
    ]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return rows_to_csv_response(f"users-{today}.csv", headers, rows)


def import_users_csv():
    file = request.files.get("file")
    rows, header_errors = parse_csv_file(
        file, ["email", "full_name", "role", "location", "education_level", "password"]
    )
    if header_errors:
        return jsonify({"errors": header_errors}), 400

    created = 0
    skipped = 0
    errors = []
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    try:
        for i, row in enumerate(rows, start=2):
            email = (row.get("email") or "").strip().lower()
            full_name = (row.get("full_name") or "").strip()
            password = row.get("password") or ""
            role = _safe_role_for_write(row.get("role"), default="seeker")

            if not email or not re.match(email_regex, email):
                errors.append({"row": i, "message": "Invalid or missing email."})
                continue
            if not full_name:
                errors.append({"row": i, "message": "full_name is required."})
                continue
            if len(str(password)) < 6:
                errors.append({"row": i, "message": "password must be at least 6 characters."})
                continue
            if role is None:
                errors.append({"row": i, "message": "role must be seeker or employer (admin not allowed)."})
                continue
            if User.query.filter_by(email=email).first():
                skipped += 1
                continue

            education = (row.get("education_level") or "").strip().lower() or None
            if education and education not in EDUCATION_LEVELS:
                errors.append({"row": i, "message": f"Invalid education_level: {education}"})
                continue

            user = User(
                email=email,
                full_name=full_name,
                role=role,
                location=(row.get("location") or "").strip() or None,
                education_level=education,
            )
            user.set_password(str(password))
            db.session.add(user)
            created += 1

        db.session.commit()
        return jsonify({"created": created, "skipped": skipped, "errors": errors}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
