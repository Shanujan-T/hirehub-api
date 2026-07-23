from datetime import datetime

from flask import current_app, jsonify, request
from flask_jwt_extended import current_user, verify_jwt_in_request
from sqlalchemy import or_

from app.extensions import db
from app.models import Application, Company, Job, JobSkill, SavedJob, Skill, UserSkill
from app.models.job_model import EXPERIENCE_LEVELS, JOB_STATUSES, JOB_TYPES
from app.utils.csv_utils import parse_csv_file, rows_to_csv_response
from app.utils.distance import haversine_km
from app.utils.geocoding import geocode_location
from app.utils.image_upload import save_image_file, validate_image_file
from app.utils.pdf_utils import document_pdf_response, table_pdf_response


def _geocode_job_location(job):
    if not job.location:
        job.latitude = None
        job.longitude = None
        return
    coords = geocode_location(job.location)
    if coords:
        job.latitude, job.longitude = coords


def _seeker_for_distance():
    verify_jwt_in_request(optional=True)
    if (
        current_user
        and getattr(current_user, "is_authenticated", True)
        and current_user.role == "seeker"
        and current_user.latitude is not None
        and current_user.longitude is not None
    ):
        return current_user
    return None


def _enrich_job_dict(job_dict, job, seeker=None):
    seeker = seeker if seeker is not None else _seeker_for_distance()
    if (
        seeker
        and job.latitude is not None
        and job.longitude is not None
    ):
        job_dict["distance_km"] = haversine_km(
            seeker.latitude,
            seeker.longitude,
            job.latitude,
            job.longitude,
        )
    return job_dict


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


def _parse_skill_ids(raw_value, form_list=None):
    if form_list:
        return form_list
    if raw_value in (None, ""):
        return []
    if isinstance(raw_value, list):
        return raw_value
    if isinstance(raw_value, str):
        return [part.strip() for part in raw_value.split(",") if part.strip()]
    return []


def _parse_job_request_data():
    if request.content_type and "multipart/form-data" in request.content_type:
        form = request.form
        data = {
            "title": form.get("title"),
            "description": form.get("description"),
            "category": form.get("category"),
            "job_type": form.get("job_type") or "full_time",
            "experience_level": form.get("experience_level") or "entry",
            "location": form.get("location"),
            "salary_min": form.get("salary_min"),
            "salary_max": form.get("salary_max"),
            "deadline": form.get("deadline"),
            "skill_ids": _parse_skill_ids(form.get("skill_ids"), form.getlist("skill_ids")),
            "remove_image": form.get("remove_image"),
        }
        return data, request.files.get("image")
    return request.get_json(silent=True), None


def _save_job_image(job, file):
    _, error = validate_image_file(file)
    if error:
        return None, error

    upload_dir = current_app.config["JOB_IMAGE_UPLOAD_FOLDER"]
    original, _ = validate_image_file(file)
    stored_name = f"{job.id}_{original}"
    _, error = save_image_file(file, upload_dir, stored_name)
    if error:
        return None, error
    job.image_url = f"/uploads/jobs/{stored_name}"
    return job.image_url, None


def get_jobs():
    query = Job.query
    q = (request.args.get("q") or "").strip().lower()
    location = (request.args.get("location") or "").strip().lower()
    category = (request.args.get("category") or "").strip().lower()
    job_type = (request.args.get("job_type") or "").strip().lower()
    experience_level = (request.args.get("experience_level") or "").strip().lower()
    company_id = request.args.get("company_id")

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Job.title.ilike(pattern),
                Job.description.ilike(pattern),
                Job.category.ilike(pattern),
            )
        )
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

    status = (request.args.get("status") or "").strip().lower()
    if status in JOB_STATUSES:
        query = query.filter(Job.status == status)

    jobs = query.order_by(Job.id.desc()).all()
    seeker = _seeker_for_distance()
    return jsonify({
        "jobs": [_enrich_job_dict(j.to_dict(), j, seeker) for j in jobs],
    }), 200


def get_salary_insights():
    role = (request.args.get("role") or request.args.get("category") or "").strip()
    location = (request.args.get("location") or "").strip()

    query = Job.query.filter(
        or_(Job.salary_min.isnot(None), Job.salary_max.isnot(None)),
    )
    if role:
        pattern = f"%{role}%"
        query = query.filter(or_(Job.title.ilike(pattern), Job.category.ilike(pattern)))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    jobs = query.all()
    if not jobs:
        return jsonify({
            "role": role or None,
            "location": location or None,
            "count": 0,
            "avg_salary_min": None,
            "avg_salary_max": None,
        }), 200

    mins = [j.salary_min for j in jobs if j.salary_min is not None]
    maxs = [j.salary_max for j in jobs if j.salary_max is not None]
    return jsonify({
        "role": role or None,
        "location": location or None,
        "count": len(jobs),
        "avg_salary_min": round(sum(mins) / len(mins)) if mins else None,
        "avg_salary_max": round(sum(maxs) / len(maxs)) if maxs else None,
    }), 200


def get_recommended_jobs():
    user_skills = UserSkill.query.filter_by(user_id=current_user.id).all()
    user_skill_ids = {us.skill_id for us in user_skills}
    skill_names = {
        us.skill_id: us.skill.name
        for us in user_skills
        if us.skill
    }
    jobs = Job.query.filter_by(status="open").all()
    scored = []
    for job in jobs:
        job_skill_ids = {js.skill_id for js in job.job_skills}
        overlap_ids = user_skill_ids & job_skill_ids
        overlap = len(overlap_ids)
        location_boost = 0
        if (
            current_user.location
            and job.location
            and current_user.location.strip().lower() == job.location.strip().lower()
        ):
            location_boost = 2
        score = overlap * 3 + location_boost
        if score > 0:
            matched_skills = [skill_names[sid] for sid in overlap_ids if sid in skill_names]
            scored.append((score, job, matched_skills))
    scored.sort(key=lambda x: (-x[0], -x[1].id))
    return jsonify({
        "jobs": [
            {**j.to_dict(), "match_score": s, "matched_skills": matched}
            for s, j, matched in scored
        ]
    }), 200


def get_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    payload = _enrich_job_dict(job.to_dict(), job)
    return jsonify({"job": payload}), 200


def get_job_applications(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    if not _can_manage_job(job):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    apps = Application.query.filter_by(job_id=job.id).order_by(Application.id.desc()).all()
    return jsonify({"applications": [a.to_dict(include_interview=True) for a in apps]}), 200


def create_job():
    data, image_file = _parse_job_request_data()
    errors = _validate_job_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    if image_file and image_file.filename:
        _, image_error = validate_image_file(image_file)
        if image_error:
            return jsonify({"errors": [image_error]}), 400

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

        if image_file and image_file.filename:
            _, image_error = _save_job_image(job, image_file)
            if image_error:
                db.session.rollback()
                return jsonify({"errors": [image_error]}), 400

        _geocode_job_location(job)
        db.session.commit()

        try:
            from app.utils.job_match_notifier import notify_job_created

            notify_job_created(job)
        except Exception as exc:
            current_app.logger.warning("Job alert notifications skipped: %s", exc)

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

    data, image_file = _parse_job_request_data()
    errors = _validate_job_payload(data, partial=True)
    if errors:
        return jsonify({"errors": errors}), 400

    if image_file and image_file.filename:
        _, image_error = validate_image_file(image_file)
        if image_error:
            return jsonify({"errors": [image_error]}), 400

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

        if data.get("remove_image") in ("1", "true", "yes"):
            job.image_url = None
        elif image_file and image_file.filename:
            _, image_error = _save_job_image(job, image_file)
            if image_error:
                return jsonify({"errors": [image_error]}), 400

        db.session.commit()
        return jsonify({"message": "Job updated successfully.", "job": job.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def upload_job_image(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    if not _can_manage_job(job):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    file = request.files.get("image")
    if not file or not file.filename:
        return jsonify({"errors": ["image is required."]}), 400

    _, image_error = validate_image_file(file)
    if image_error:
        return jsonify({"errors": [image_error]}), 400

    try:
        _, image_error = _save_job_image(job, file)
        if image_error:
            return jsonify({"errors": [image_error]}), 400
        db.session.commit()
        return jsonify({
            "message": "Job image uploaded.",
            "job": job.to_dict(),
        }), 200
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


def get_similar_jobs(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404

    source_skill_ids = {js.skill_id for js in job.job_skills}
    if not source_skill_ids:
        return jsonify({"jobs": []}), 200

    candidates = (
        Job.query.filter(Job.id != job.id, Job.status == "open")
        .order_by(Job.id.desc())
        .all()
    )
    scored = []
    for other in candidates:
        other_skill_ids = {js.skill_id for js in other.job_skills}
        overlap = len(source_skill_ids & other_skill_ids)
        if overlap > 0:
            scored.append((overlap, other))
    scored.sort(key=lambda x: (-x[0], -x[1].id))
    top = scored[:3]
    return jsonify({"jobs": [j.to_dict() for _, j in top]}), 200


def export_job_applicants_csv(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    if not _can_manage_job(job):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    apps = Application.query.filter_by(job_id=job.id).order_by(Application.id).all()
    headers = [
        "candidate_name",
        "email",
        "location",
        "education",
        "cover_letter",
        "status",
        "applied_date",
    ]
    rows = []
    for app_row in apps:
        seeker = app_row.seeker
        rows.append([
            seeker.full_name if seeker else "",
            seeker.email if seeker else "",
            seeker.location or "" if seeker else "",
            seeker.education_level or "" if seeker else "",
            app_row.cover_letter or "",
            app_row.status,
            app_row.created_at.isoformat() if app_row.created_at else "",
        ])
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return rows_to_csv_response(f"job-{job.id}-applicants-{today}.csv", headers, rows)


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
