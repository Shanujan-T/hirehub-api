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


def create_job():
    data = request.get_json(silent=True)
    errors = _validate_job_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    company = Company.query.filter_by(owner_id=current_user.id).first()
    if not company:
        return jsonify({"error": "Create a company profile before posting jobs."}), 400

    try:
        deadline = _parse_date(data.get("deadline"))
        job = Job(
            company_id=company.id,
            posted_by=current_user.id,
            title=str(data.get("title")).strip(),
            description=data.get("description"),
            category=(str(data.get("category")).strip() if data.get("category") else None),
            job_type=str(data.get("job_type") or "full_time").strip().lower(),
            experience_level=str(data.get("experience_level") or "entry").strip().lower(),
            location=(str(data.get("location")).strip() if data.get("location") else None),
            salary_min=int(data["salary_min"]) if data.get("salary_min") not in (None, "") else None,
            salary_max=int(data["salary_max"]) if data.get("salary_max") not in (None, "") else None,
            deadline=deadline if deadline != "invalid" else None,
            status="open",
        )
        db.session.add(job)
        db.session.flush()
        _attach_skills(job, data.get("skill_ids") or [])
        db.session.commit()
        return jsonify({"message": "Job created successfully.", "job": job.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def update_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    if not _can_manage_job(job):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    data = request.get_json(silent=True)
    errors = _validate_job_payload(data, partial=True)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        if "title" in data:
            job.title = str(data.get("title")).strip()
        if "description" in data:
            job.description = data.get("description")
        if "category" in data:
            job.category = str(data.get("category")).strip() if data.get("category") else None
        if "job_type" in data:
            job.job_type = str(data.get("job_type")).strip().lower()
        if "experience_level" in data:
            job.experience_level = str(data.get("experience_level")).strip().lower()
        if "location" in data:
            job.location = str(data.get("location")).strip() if data.get("location") else None
        if "salary_min" in data:
            job.salary_min = int(data["salary_min"]) if data.get("salary_min") not in (None, "") else None
        if "salary_max" in data:
            job.salary_max = int(data["salary_max"]) if data.get("salary_max") not in (None, "") else None
        if "deadline" in data:
            d = _parse_date(data.get("deadline"))
            job.deadline = None if d in (None, "invalid") else d
        if "skill_ids" in data:
            _attach_skills(job, data.get("skill_ids") or [])
        db.session.commit()
        return jsonify({"message": "Job updated successfully.", "job": job.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def patch_job_status(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    if not _can_manage_job(job):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    data = request.get_json(silent=True) or {}
    status = str(data.get("status") or "").strip().lower()
    if status not in JOB_STATUSES:
        return jsonify({"errors": [f"status must be one of: {', '.join(JOB_STATUSES)}."]}), 400
    try:
        job.status = status
        db.session.commit()
        return jsonify({"message": "Job status updated.", "job": job.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def delete_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    if not _can_manage_job(job):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    try:
        db.session.delete(job)
        db.session.commit()
        return jsonify({"message": "Job deleted successfully."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def export_job_pdf(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    skills = ", ".join(js.skill.name for js in job.job_skills if js.skill) or "—"
    company_name = job.company.name if job.company else "—"
    sections = [
        ("Company", company_name),
        ("Title", job.title),
        ("Type", job.job_type),
        ("Experience", job.experience_level),
        ("Location", job.location or "—"),
        ("Salary", f"{job.salary_min or '—'} - {job.salary_max or '—'}"),
        ("Deadline", job.deadline.isoformat() if job.deadline else "—"),
        ("Status", job.status),
        ("Required skills", skills),
        ("Description", job.description or "—"),
    ]
    return document_pdf_response(f"job-{job.id}.pdf", f"Job Flyer — {job.title}", sections)


def export_jobs():
    if current_user.role == "admin":
        jobs = Job.query.order_by(Job.id.desc()).all()
    else:
        jobs = Job.query.filter_by(posted_by=current_user.id).order_by(Job.id.desc()).all()

    headers = ["id", "title", "category", "job_type", "experience_level", "location", "status", "company_id"]
    rows = [
        [j.id, j.title, j.category or "", j.job_type, j.experience_level, j.location or "", j.status, j.company_id]
        for j in jobs
    ]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if (request.args.get("format") or "csv").lower() == "pdf":
        open_jobs = [j for j in jobs if j.status == "open"]
        pdf_rows = [
            [j.title, j.job_type, j.experience_level, j.location or "", j.category or ""]
            for j in open_jobs
        ]
        return table_pdf_response(
            f"jobs-{today}.pdf",
            "Jobs Board",
            ["Title", "Type", "Experience", "Location", "Category"],
            pdf_rows,
        )
    return rows_to_csv_response(f"jobs-{today}.csv", headers, rows)


def import_jobs_csv():
    company = Company.query.filter_by(owner_id=current_user.id).first()
    if not company:
        return jsonify({"error": "Create a company profile before importing jobs."}), 400

    file = request.files.get("file")
    rows, header_errors = parse_csv_file(
        file,
        ["title", "category", "job_type", "experience_level", "location", "salary_min", "salary_max", "deadline", "description"],
    )
    if header_errors:
        return jsonify({"errors": header_errors}), 400

    created = skipped = 0
    errors = []
    try:
        for i, row in enumerate(rows, start=2):
            title = (row.get("title") or "").strip()
            if not title:
                errors.append({"row": i, "message": "title is required."})
                continue
            jt = (row.get("job_type") or "full_time").strip().lower()
            el = (row.get("experience_level") or "entry").strip().lower()
            if jt not in JOB_TYPES:
                errors.append({"row": i, "message": f"Invalid job_type: {jt}"})
                continue
            if el not in EXPERIENCE_LEVELS:
                errors.append({"row": i, "message": f"Invalid experience_level: {el}"})
                continue
            deadline = _parse_date(row.get("deadline"))
            if deadline == "invalid":
                errors.append({"row": i, "message": "Invalid deadline (use YYYY-MM-DD)."})
                continue
            salary_min = salary_max = None
            try:
                if row.get("salary_min"):
                    salary_min = int(row.get("salary_min"))
                if row.get("salary_max"):
                    salary_max = int(row.get("salary_max"))
            except ValueError:
                errors.append({"row": i, "message": "salary_min/salary_max must be integers."})
                continue

            job = Job(
                company_id=company.id,
                posted_by=current_user.id,
                title=title,
                category=(row.get("category") or "").strip() or None,
                job_type=jt,
                experience_level=el,
                location=(row.get("location") or "").strip() or None,
                salary_min=salary_min,
                salary_max=salary_max,
                deadline=deadline,
                description=(row.get("description") or "").strip() or None,
                status="open",
            )
            db.session.add(job)
            created += 1
        db.session.commit()
        return jsonify({"created": created, "skipped": skipped, "errors": errors}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def save_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    if SavedJob.query.filter_by(seeker_id=current_user.id, job_id=job.id).first():
        return jsonify({"error": "Job already saved."}), 400
    try:
        row = SavedJob(seeker_id=current_user.id, job_id=job.id)
        db.session.add(row)
        db.session.commit()
        return jsonify({"message": "Job saved.", "saved_job": row.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def unsave_job(job_id):
    row = SavedJob.query.filter_by(seeker_id=current_user.id, job_id=job_id).first()
    if not row:
        return jsonify({"error": "Saved job not found."}), 404
    try:
        db.session.delete(row)
        db.session.commit()
        return jsonify({"message": "Job unsaved."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def get_my_saved_jobs():
    rows = SavedJob.query.filter_by(seeker_id=current_user.id).order_by(SavedJob.id.desc()).all()
    return jsonify({"saved_jobs": [r.to_dict() for r in rows]}), 200
