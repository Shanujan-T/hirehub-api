from flask import jsonify, request

from app.extensions import db
from app.models import Interest


def _validate_interest_payload(data, interest_id=None):
    errors = []
    if not data:
        return ["Request body is required."]
    name = data.get("name")
    if name is None or str(name).strip() == "":
        errors.append("name is required.")
    else:
        existing = Interest.query.filter_by(name=str(name).strip()).first()
        if existing and (interest_id is None or existing.id != interest_id):
            errors.append("Interest name already exists.")
    return errors


def get_interests():
    q = (request.args.get("q") or "").strip().lower()
    category = (request.args.get("category") or "").strip().lower()
    query = Interest.query
    if q:
        query = query.filter(Interest.name.ilike(f"%{q}%"))
    if category:
        query = query.filter(Interest.category.ilike(f"%{category}%"))
    return jsonify({"interests": [i.to_dict() for i in query.order_by(Interest.name).all()]}), 200


def get_interest(interest_id):
    interest = db.session.get(Interest, interest_id)
    if not interest:
        return jsonify({"error": "Interest not found."}), 404
    return jsonify({"interest": interest.to_dict()}), 200


def create_interest():
    data = request.get_json(silent=True)
    errors = _validate_interest_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400
    try:
        interest = Interest(
            name=str(data.get("name")).strip(),
            category=(str(data.get("category")).strip() if data.get("category") else None),
        )
        db.session.add(interest)
        db.session.commit()
        return jsonify({"message": "Interest created successfully.", "interest": interest.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def update_interest(interest_id):
    interest = db.session.get(Interest, interest_id)
    if not interest:
        return jsonify({"error": "Interest not found."}), 404
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400
    errors = _validate_interest_payload(data, interest_id=interest.id) if "name" in data else []
    if errors:
        return jsonify({"errors": errors}), 400
    try:
        if "name" in data:
            interest.name = str(data.get("name")).strip()
        if "category" in data:
            interest.category = str(data.get("category")).strip() if data.get("category") else None
        db.session.commit()
        return jsonify({"message": "Interest updated successfully.", "interest": interest.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def delete_interest(interest_id):
    interest = db.session.get(Interest, interest_id)
    if not interest:
        return jsonify({"error": "Interest not found."}), 404
    try:
        db.session.delete(interest)
        db.session.commit()
        return jsonify({"message": "Interest deleted successfully."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
