import os
import re
import secrets

from werkzeug.utils import secure_filename

from flask import current_app, jsonify, request
from flask_jwt_extended import create_access_token, current_user

from app.extensions import db
from app.models import PasswordReset, User
from app.models.user_model import EDUCATION_LEVELS, PUBLIC_REGISTER_ROLES
from app.utils import utc_now
from app.utils.image_upload import save_entity_image, validate_image_file

def _resolve_public_role(data):
    """
    Map account type chosen at signup to seeker|employer.
    Ignores/rejects any attempt to set role=admin via the request body.
    Accepts either `role` or `account_type`. Aliases jobseeker → seeker.
    """
    raw = data.get("account_type", data.get("role", "seeker"))
    role = str(raw or "seeker").strip().lower()
    if role in ("jobseeker", "job_seeker", "seeker"):
        return "seeker"
    if role == "employer":
        return "employer"
    # Explicit admin (or anything else) is rejected — never assigned from public register
    return None


def _validate_register_payload(data):
    errors = []
    if not data:
        return ["Request body is required."]

    email = data.get("email")
    if email is None or str(email).strip() == "":
        errors.append("email is required.")
    else:
        email_str = str(email).strip().lower()
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, email_str):
            errors.append("Invalid email format.")
        elif User.query.filter_by(email=email_str).first():
            errors.append("Email address already exists.")

    password = data.get("password")
    if password is None or str(password).strip() == "":
        errors.append("password is required.")
    elif len(str(password)) < 6:
        errors.append("password must be at least 6 characters long.")

    full_name = data.get("full_name")
    if full_name is None or str(full_name).strip() == "":
        errors.append("full_name is required.")

    if "role" in data or "account_type" in data:
        resolved = _resolve_public_role(data)
        if resolved is None:
            errors.append("role must be 'seeker' or 'employer'. Admin accounts cannot be created via registration.")
        elif resolved not in PUBLIC_REGISTER_ROLES:
            errors.append("role must be 'seeker' or 'employer'.")

    return errors


def _validate_login_payload(data):
    errors = []
    if not data:
        return ["Request body is required."]
    if data.get("email") is None or str(data.get("email")).strip() == "":
        errors.append("email is required.")
    if data.get("password") is None or str(data.get("password")).strip() == "":
        errors.append("password is required.")
    return errors


def _profile_updatable_fields(data, user):
    """Build allowed profile updates. Never accepts or changes `role`."""
    errors = []
    updates = {}

    if "full_name" in data:
        name = str(data.get("full_name") or "").strip()
        if not name:
            errors.append("full_name cannot be empty.")
        else:
            updates["full_name"] = name

    if "bio" in data:
        updates["bio"] = data.get("bio")

    if "location" in data:
        updates["location"] = (str(data.get("location")).strip() if data.get("location") else None)

    if "phone" in data:
        updates["phone"] = (str(data.get("phone")).strip() if data.get("phone") else None)

    if "education_level" in data:
        level = data.get("education_level")
        if level in (None, ""):
            updates["education_level"] = None
        else:
            level = str(level).strip().lower()
            if level not in EDUCATION_LEVELS:
                errors.append(f"education_level must be one of: {', '.join(EDUCATION_LEVELS)}.")
            else:
                updates["education_level"] = level

    if "resume_url" in data:
        updates["resume_url"] = (str(data.get("resume_url")).strip() if data.get("resume_url") else None)

    if "avatar_url" in data:
        updates["avatar_url"] = (str(data.get("avatar_url")).strip() if data.get("avatar_url") else None)

    if "password" in data and data.get("password") is not None and str(data.get("password")).strip() != "":
        if len(str(data.get("password"))) < 6:
            errors.append("password must be at least 6 characters long.")
        else:
            updates["password"] = str(data.get("password"))

    # role / is_active / email elevation are intentionally ignored or blocked
    if "role" in data:
        errors.append("role cannot be changed via profile update.")

    return updates, errors


def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    errors = _validate_register_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    # Hard-code role from account type; never trust client for admin
    role = _resolve_public_role(data) or "seeker"

    try:
        user = User(
            email=str(data.get("email")).strip().lower(),
            full_name=str(data.get("full_name")).strip(),
            location=(str(data.get("location")).strip() if data.get("location") else None),
            role=role,
        )
        user.set_password(str(data.get("password")))
        db.session.add(user)
        db.session.commit()
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            "message": "User registered successfully.",
            "access_token": access_token,
            "user": user.to_dict(),
        }), 201
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Registration failed: %s", exc)
        return jsonify({"error": "An internal server error occurred."}), 500


def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    errors = _validate_login_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        email_str = str(data.get("email")).strip().lower()
        user = User.query.filter_by(email=email_str).first()

        if not user or not user.check_password(str(data.get("password"))):
            return jsonify({"error": "Invalid email or password."}), 401

        if not user.is_active:
            return jsonify({"error": "Account is deactivated."}), 403

        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            "message": "Login successful.",
            "access_token": access_token,
            "user": user.to_dict(),
        }), 200
    except Exception:
        return jsonify({"error": "An internal server error occurred."}), 500


def logout():
    # Stateless JWT — client discards the token
    return jsonify({"message": "Logged out successfully."}), 200


def get_profile():
    return jsonify({"user": current_user.to_dict(include_skills=True)}), 200


def update_profile():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    updates, errors = _profile_updatable_fields(data, current_user)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        password = updates.pop("password", None)
        for key, value in updates.items():
            setattr(current_user, key, value)
        if password:
            current_user.set_password(password)
        db.session.commit()
        return jsonify({"message": "Profile updated successfully.", "user": current_user.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


ALLOWED_RESUME_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_RESUME_BYTES = 5 * 1024 * 1024


def upload_resume():
    if current_user.role != "seeker":
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"errors": ["file is required."]}), 400

    original = secure_filename(file.filename)
    ext = os.path.splitext(original)[1].lower()
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        return jsonify({"errors": ["Resume must be PDF, DOC, or DOCX."]}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_RESUME_BYTES:
        return jsonify({"errors": ["Resume file must be 5MB or smaller."]}), 400

    upload_dir = current_app.config["RESUME_UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    stored_name = f"{current_user.id}_{original}"
    file_path = os.path.join(upload_dir, stored_name)
    file.save(file_path)

    resume_url = f"/uploads/resumes/{stored_name}"
    try:
        current_user.resume_url = resume_url
        db.session.commit()
        return jsonify({
            "message": "Resume uploaded successfully.",
            "resume_url": resume_url,
            "user": current_user.to_dict(),
        }), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def upload_avatar():
    file = request.files.get("avatar") or request.files.get("file")
    if not file or not file.filename:
        return jsonify({"errors": ["avatar is required."]}), 400

    _, error = validate_image_file(file)
    if error:
        return jsonify({"errors": [error]}), 400

    try:
        url, error = save_entity_image(
            file,
            current_app.config["USER_AVATAR_UPLOAD_FOLDER"],
            current_user.id,
            "/uploads/users",
        )
        if error:
            return jsonify({"errors": [error]}), 400
        current_user.avatar_url = url
        db.session.commit()
        return jsonify({
            "message": "Profile photo uploaded.",
            "user": current_user.to_dict(),
        }), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def forgot_password():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    email = data.get("email")
    if email is None or str(email).strip() == "":
        return jsonify({"errors": ["email is required."]}), 400

    email_str = str(email).strip().lower()
    user = User.query.filter_by(email=email_str).first()
    if not user:
        return jsonify({
            "message": "If that email is registered, a password reset token has been generated.",
        }), 200

    try:
        from flask import current_app

        PasswordReset.query.filter_by(user_id=user.id, used_at=None).delete()
        raw_token = secrets.token_urlsafe(32)
        expires_at = utc_now() + current_app.config["PASSWORD_RESET_TOKEN_EXPIRES"]
        reset = PasswordReset(user_id=user.id, expires_at=expires_at)
        reset.set_token(raw_token)
        db.session.add(reset)
        db.session.commit()
        return jsonify({
            "message": "Password reset token generated.",
            "reset_token": raw_token,
            "expires_at": expires_at.isoformat(),
        }), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def reset_password():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    errors = []
    email = data.get("email")
    token = data.get("token")
    password = data.get("password") or data.get("new_password")

    if email is None or str(email).strip() == "":
        errors.append("email is required.")
    if token is None or str(token).strip() == "":
        errors.append("token is required.")
    if password is None or str(password).strip() == "":
        errors.append("password is required.")
    elif len(str(password)) < 6:
        errors.append("password must be at least 6 characters long.")

    if errors:
        return jsonify({"errors": errors}), 400

    user = User.query.filter_by(email=str(email).strip().lower()).first()
    if not user:
        return jsonify({"error": "Invalid or expired reset token."}), 400

    reset = (
        PasswordReset.query.filter_by(user_id=user.id, used_at=None)
        .order_by(PasswordReset.id.desc())
        .first()
    )
    if not reset or not reset.is_valid() or not reset.check_token(str(token)):
        return jsonify({"error": "Invalid or expired reset token."}), 400

    try:
        user.set_password(str(password))
        reset.used_at = utc_now()
        db.session.commit()
        return jsonify({"message": "Password reset successfully."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
