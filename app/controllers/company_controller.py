from datetime import datetime

from flask import jsonify, request
from flask_jwt_extended import current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Company
from app.utils.csv_utils import rows_to_csv_response


def _validate_company_payload(data, company_id=None):
    errors = []
    if not data:
        return ["Request body is required."]

    name = data.get("name")
    if name is None or str(name).strip() == "":
        errors.append("name is required.")
    else:
        name_str = str(name).strip()
        existing = Company.query.filter_by(name=name_str).first()
        if existing and (company_id is None or existing.id != company_id):
            errors.append("Company name already exists.")

    return errors


def get_companies():
    q = (request.args.get("q") or "").strip().lower()
    industry = (request.args.get("industry") or "").strip().lower()
    location = (request.args.get("location") or "").strip().lower()

    query = Company.query
    if q:
        query = query.filter(
            or_(Company.name.ilike(f"%{q}%"), Company.description.ilike(f"%{q}%"))
        )
    if industry:
        query = query.filter(Company.industry.ilike(f"%{industry}%"))
    if location:
        query = query.filter(Company.location.ilike(f"%{location}%"))

    companies = query.order_by(Company.id.desc()).all()
    return jsonify({"companies": [c.to_dict() for c in companies]}), 200


def get_company(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        return jsonify({"error": "Company not found."}), 404
    return jsonify({"company": company.to_dict(include_jobs=True)}), 200


def get_my_company():
    company = Company.query.filter_by(owner_id=current_user.id).first()
    if not company:
        return jsonify({"error": "Company not found."}), 404
    return jsonify({"company": company.to_dict(include_jobs=True)}), 200
