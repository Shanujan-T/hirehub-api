from datetime import datetime

from flask import jsonify, request
from flask_jwt_extended import current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Application, Company, Job, JobSkill, SavedJob, Skill, UserSkill
from app.models.job_model import EXPERIENCE_LEVELS, JOB_STATUSES, JOB_TYPES
from app.utils.csv_utils import parse_csv_file, rows_to_csv_response
from app.utils.pdf_utils import document_pdf_response, table_pdf_response


def _parse_date(value):
    if value in (None, ""):
        return None
    if hasattr(value, "isoformat"):
        return value
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return "invalid"


def _validate_job_payload(data, partial=False):
    errors = []
    if not data:
        return ["Request body is required."]

    if not partial or "title" in data:
        if not data.get("title") or str(data.get("title")).strip() == "":
            errors.append("title is required.")

    if "job_type" in data or not partial:
        jt = str(data.get("job_type") or "full_time").strip().lower()
        if jt not in JOB_TYPES:
            errors.append(f"job_type must be one of: {', '.join(JOB_TYPES)}.")

    if "experience_level" in data or not partial:
        el = str(data.get("experience_level") or "entry").strip().lower()
        if el not in EXPERIENCE_LEVELS:
            errors.append(f"experience_level must be one of: {', '.join(EXPERIENCE_LEVELS)}.")

    if "deadline" in data:
        d = _parse_date(data.get("deadline"))
        if d == "invalid":
            errors.append("deadline must be YYYY-MM-DD.")

    if "salary_min" in data and data.get("salary_min") not in (None, ""):
        try:
            int(data.get("salary_min"))
        except (TypeError, ValueError):
            errors.append("salary_min must be an integer.")

    if "salary_max" in data and data.get("salary_max") not in (None, ""):
        try:
            int(data.get("salary_max"))
        except (TypeError, ValueError):
            errors.append("salary_max must be an integer.")

    return errors


def _attach_skills(job, skill_ids):
    JobSkill.query.filter_by(job_id=job.id).delete()
    seen = set()
    for sid in skill_ids or []:
        try:
            sid = int(sid)
        except (TypeError, ValueError):
            continue
        if sid in seen:
            continue
        if not db.session.get(Skill, sid):
            continue
        seen.add(sid)
        db.session.add(JobSkill(job_id=job.id, skill_id=sid))


def _can_manage_job(job):
    return current_user.role == "admin" or (
        current_user.role == "employer" and job.posted_by == current_user.id
    )


def get_jobs():
    query = Job.query
    q = (request.args.get("q") or "").strip().lower()
    location = (request.args.get("location") or "").strip().lower()
    category = (request.args.get("category") or "").strip().lower()
    job_type = (request.args.get("job_type") or "").strip().lower()
    experience_level = (request.args.get("experience_level") or "").strip().lower()
    company_id = request.args.get("company_id")

    if q:
        query = query.filter(or_(Job.title.ilike(f"%{q}%"), Job.description.ilike(f"%{q}%")))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if category:
        query = query.filter(Job.category.ilike(f"%{category}%"))
    if job_type:
        query = query.filter(Job.job_type == job_type)
    if experience_level:
        query = query.filter(Job.experience_level == experience_level)
    if company_id:
        try:
            query = query.filter(Job.company_id == int(company_id))
        except ValueError:
            pass

    jobs = query.order_by(Job.id.desc()).all()
    return jsonify({"jobs": [j.to_dict() for j in jobs]}), 200


def get_recommended_jobs():
    user_skill_ids = {us.skill_id for us in UserSkill.query.filter_by(user_id=current_user.id).all()}
    jobs = Job.query.filter_by(status="open").all()
    scored = []
    for job in jobs:
        job_skill_ids = {js.skill_id for js in job.job_skills}
        overlap = len(user_skill_ids & job_skill_ids)
        location_boost = 0
        if (
            current_user.location
            and job.location
            and current_user.location.strip().lower() == job.location.strip().lower()
        ):
            location_boost = 2
        score = overlap * 3 + location_boost
        if score > 0:
            scored.append((score, job))
    scored.sort(key=lambda x: (-x[0], -x[1].id))
    return jsonify({
        "jobs": [{**j.to_dict(), "match_score": s} for s, j in scored]
    }), 200


def get_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    return jsonify({"job": job.to_dict()}), 200


def get_job_applications(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    if not _can_manage_job(job):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    apps = Application.query.filter_by(job_id=job.id).order_by(Application.id.desc()).all()
    return jsonify({"applications": [a.to_dict() for a in apps]}), 200
