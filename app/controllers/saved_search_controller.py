from flask import jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import SavedSearch
from app.models.job_model import JOB_TYPES


def _validate_saved_search_payload(data, partial=False):
    errors = []
    if not data:
        return ["Request body is required."]

    if not partial:
        has_criterion = any(
            data.get(field) not in (None, "")
            for field in ("keywords", "category", "location", "job_type", "min_salary")
        )
        if not has_criterion:
            errors.append("At least one search criterion is required.")

    if "job_type" in data and data.get("job_type") not in (None, ""):
        jt = str(data.get("job_type")).strip().lower()
        if jt not in JOB_TYPES:
            errors.append(f"job_type must be one of: {', '.join(JOB_TYPES)}.")

    if "min_salary" in data and data.get("min_salary") not in (None, ""):
        try:
            int(data.get("min_salary"))
        except (TypeError, ValueError):
            errors.append("min_salary must be an integer.")

    return errors


def _apply_saved_search_fields(row, data):
    if "keywords" in data:
        row.keywords = str(data.get("keywords")).strip() if data.get("keywords") not in (None, "") else None
    if "category" in data:
        row.category = str(data.get("category")).strip() if data.get("category") not in (None, "") else None
    if "location" in data:
        row.location = str(data.get("location")).strip() if data.get("location") not in (None, "") else None
    if "job_type" in data:
        row.job_type = (
            str(data.get("job_type")).strip().lower()
            if data.get("job_type") not in (None, "")
            else None
        )
    if "min_salary" in data:
        row.min_salary = (
            int(data.get("min_salary"))
            if data.get("min_salary") not in (None, "")
            else None
        )


def get_my_saved_searches():
    rows = (
        SavedSearch.query.filter_by(user_id=current_user.id)
        .order_by(SavedSearch.id.desc())
        .all()
    )
    return jsonify({"saved_searches": [r.to_dict() for r in rows]}), 200


def get_my_saved_search(saved_search_id):
    row = db.session.get(SavedSearch, saved_search_id)
    if not row or row.user_id != current_user.id:
        return jsonify({"error": "Saved search not found."}), 404
    return jsonify({"saved_search": row.to_dict()}), 200


def create_my_saved_search():
    data = request.get_json(silent=True)
    errors = _validate_saved_search_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        row = SavedSearch(user_id=current_user.id)
        _apply_saved_search_fields(row, data)
        db.session.add(row)
        db.session.commit()
        return jsonify({
            "message": "Saved search created.",
            "saved_search": row.to_dict(),
        }), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def update_my_saved_search(saved_search_id):
    row = db.session.get(SavedSearch, saved_search_id)
    if not row or row.user_id != current_user.id:
        return jsonify({"error": "Saved search not found."}), 404

    data = request.get_json(silent=True)
    errors = _validate_saved_search_payload(data, partial=True)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        _apply_saved_search_fields(row, data)
        db.session.commit()
        return jsonify({
            "message": "Saved search updated.",
            "saved_search": row.to_dict(),
        }), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def delete_my_saved_search(saved_search_id):
    row = db.session.get(SavedSearch, saved_search_id)
    if not row or row.user_id != current_user.id:
        return jsonify({"error": "Saved search not found."}), 404

    try:
        db.session.delete(row)
        db.session.commit()
        return jsonify({"message": "Saved search deleted."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
