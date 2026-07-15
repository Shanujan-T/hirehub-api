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
