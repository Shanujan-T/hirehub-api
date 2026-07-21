from datetime import datetime

from flask import current_app, jsonify, request
from flask_jwt_extended import current_user
from sqlalchemy import func, or_

from app.extensions import db
from app.models import Company, Job
from app.utils.csv_utils import rows_to_csv_response
from app.utils.image_upload import save_image_file, validate_image_file


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
    open_counts = dict(
        db.session.query(Job.company_id, func.count(Job.id))
        .filter(Job.status == "open")
        .group_by(Job.company_id)
        .all()
    )
    return jsonify({
        "companies": [
            c.to_dict(open_jobs_count=int(open_counts.get(c.id, 0)))
            for c in companies
        ]
    }), 200


def get_company(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        return jsonify({"error": "Company not found."}), 404
    open_count = (
        Job.query.filter_by(company_id=company.id, status="open").count()
    )
    data = company.to_dict(include_jobs=True, open_jobs_count=open_count)
    return jsonify({"company": data}), 200


def get_my_company():
    company = Company.query.filter_by(owner_id=current_user.id).first()
    if not company:
        return jsonify({"error": "Company not found."}), 404
    return jsonify({"company": company.to_dict(include_jobs=True)}), 200


def create_company():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    if Company.query.filter_by(owner_id=current_user.id).first():
        return jsonify({"error": "Employer already has a company profile."}), 400

    errors = _validate_company_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        company = Company(
            owner_id=current_user.id,
            name=str(data.get("name")).strip(),
            industry=(str(data.get("industry")).strip() if data.get("industry") else None),
            description=data.get("description"),
            website=(str(data.get("website")).strip() if data.get("website") else None),
            location=(str(data.get("location")).strip() if data.get("location") else None),
            logo_url=(str(data.get("logo_url")).strip() if data.get("logo_url") else None),
        )
        db.session.add(company)
        db.session.commit()
        return jsonify({"message": "Company created successfully.", "company": company.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def update_company(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        return jsonify({"error": "Company not found."}), 404

    is_owner = company.owner_id == current_user.id and current_user.role == "employer"
    if not is_owner and current_user.role != "admin":
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    errors = _validate_company_payload(data, company_id=company.id) if "name" in data else []
    if "name" in data and (data.get("name") is None or str(data.get("name")).strip() == ""):
        errors.append("name cannot be empty.")
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        for field in ("name", "industry", "description", "website", "location", "logo_url"):
            if field in data:
                val = data.get(field)
                if field == "name":
                    company.name = str(val).strip()
                elif field == "description":
                    company.description = val
                else:
                    setattr(company, field, str(val).strip() if val not in (None, "") else None)
        db.session.commit()
        return jsonify({"message": "Company updated successfully.", "company": company.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def delete_company(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        return jsonify({"error": "Company not found."}), 404
    try:
        db.session.delete(company)
        db.session.commit()
        return jsonify({"message": "Company deleted successfully."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def export_companies_csv():
    companies = Company.query.order_by(Company.id).all()
    headers = ["name", "industry", "location", "website", "owner_id"]
    rows = [
        [c.name, c.industry or "", c.location or "", c.website or "", c.owner_id]
        for c in companies
    ]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return rows_to_csv_response(f"companies-{today}.csv", headers, rows)


def verify_company(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        return jsonify({"error": "Company not found."}), 404

    data = request.get_json(silent=True) or {}
    is_verified = data.get("is_verified", True)
    if not isinstance(is_verified, bool):
        return jsonify({"errors": ["is_verified must be a boolean."]}), 400

    try:
        company.is_verified = is_verified
        db.session.commit()
        return jsonify({
            "message": "Company verification updated.",
            "company": company.to_dict(),
        }), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def _can_manage_company(company):
    return current_user.role == "admin" or (
        current_user.role == "employer" and company.owner_id == current_user.id
    )


def _save_company_logo(company, file):
    _, error = validate_image_file(file)
    if error:
        return None, error
    original, _ = validate_image_file(file)
    stored_name = f"{company.id}_{original}"
    upload_dir = current_app.config["COMPANY_LOGO_UPLOAD_FOLDER"]
    _, error = save_image_file(file, upload_dir, stored_name)
    if error:
        return None, error
    company.logo_url = f"/uploads/companies/{stored_name}"
    return company.logo_url, None


def upload_company_logo(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        return jsonify({"error": "Company not found."}), 404
    if not _can_manage_company(company):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    file = request.files.get("logo")
    if not file or not file.filename:
        return jsonify({"errors": ["logo is required."]}), 400

    _, error = validate_image_file(file)
    if error:
        return jsonify({"errors": [error]}), 400

    try:
        _, error = _save_company_logo(company, file)
        if error:
            return jsonify({"errors": [error]}), 400
        db.session.commit()
        open_count = Job.query.filter_by(company_id=company.id, status="open").count()
        return jsonify({
            "message": "Company logo uploaded.",
            "company": company.to_dict(open_jobs_count=open_count),
        }), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
