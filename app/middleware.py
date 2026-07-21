from functools import wraps

from flask import jsonify
from flask_jwt_extended import current_user, verify_jwt_in_request


def roles_required(*roles):
    """Require JWT auth and that current_user.role is one of *roles."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            if not current_user:
                return jsonify({"error": "User not found."}), 404
            if not current_user.is_active:
                return jsonify({"error": "Account is deactivated."}), 403
            if current_user.role not in roles:
                return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_role(*roles):
    """Alias for roles_required — e.g. @require_role('admin')."""
    return roles_required(*roles)


def jwt_required_active(fn):
    """Require a valid JWT and an active user (any role)."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        if not current_user:
            return jsonify({"error": "User not found."}), 404
        if not current_user.is_active:
            return jsonify({"error": "Account is deactivated."}), 403
        return fn(*args, **kwargs)

    return wrapper


def jwt_optional(fn):
    """Load JWT identity when present; allow unauthenticated access."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request(optional=True)
        return fn(*args, **kwargs)

    return wrapper
