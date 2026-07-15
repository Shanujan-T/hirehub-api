from collections import Counter

from flask import jsonify
from flask_jwt_extended import current_user

from app.models import Application, Company, Job, Post, Report, User, UserSkill
from app.utils.pdf_utils import document_pdf_response


def _seeker_dashboard():
    apps = Application.query.filter_by(seeker_id=current_user.id).all()
    by_status = Counter(a.status for a in apps)
    # Reuse recommendation logic without returning a Response
    from app.models import Job as JobModel

    user_skill_ids = {us.skill_id for us in UserSkill.query.filter_by(user_id=current_user.id).all()}
    recommended = []
    for job in JobModel.query.filter_by(status="open").all():
        overlap = len(user_skill_ids & {js.skill_id for js in job.job_skills})
        boost = 0
        if (
            current_user.location
            and job.location
            and current_user.location.strip().lower() == job.location.strip().lower()
        ):
            boost = 2
        score = overlap * 3 + boost
        if score > 0:
            recommended.append((score, job))
    recommended.sort(key=lambda x: (-x[0], -x[1].id))

    return {
        "role": "seeker",
        "applications_by_status": dict(by_status),
        "applications": [a.to_dict() for a in apps[:20]],
        "recommended_jobs": [{**j.to_dict(), "match_score": s} for s, j in recommended[:10]],
    }


def _employer_dashboard():
    jobs = Job.query.filter_by(posted_by=current_user.id).all()
    job_ids = [j.id for j in jobs]
    apps = Application.query.filter(Application.job_id.in_(job_ids)).all() if job_ids else []
    return {
        "role": "employer",
        "jobs_count": len(jobs),
        "jobs": [j.to_dict() for j in jobs],
        "applicants_by_status": dict(Counter(a.status for a in apps)),
        "applications": [a.to_dict() for a in apps[:30]],
        "company": Company.query.filter_by(owner_id=current_user.id).first(),
    }


def _admin_dashboard():
    return {
        "role": "admin",
        "counts": {
            "users": User.query.count(),
            "seekers": User.query.filter_by(role="seeker").count(),
            "employers": User.query.filter_by(role="employer").count(),
            "companies": Company.query.count(),
            "jobs": Job.query.count(),
            "applications": Application.query.count(),
            "posts": Post.query.count(),
            "open_reports": Report.query.filter_by(status="open").count(),
        },
    }


def get_dashboard():
    if current_user.role == "seeker":
        data = _seeker_dashboard()
    elif current_user.role == "employer":
        data = _employer_dashboard()
        if data.get("company"):
            data["company"] = data["company"].to_dict()
    else:
        data = _admin_dashboard()
    return jsonify({"dashboard": data}), 200


def export_dashboard_pdf():
    if current_user.role == "seeker":
        data = _seeker_dashboard()
        sections = [
            ("Applications by status", str(data["applications_by_status"])),
            ("Recommended jobs", str(len(data["recommended_jobs"]))),
        ]
        for job in data["recommended_jobs"][:5]:
            sections.append((job.get("title"), f"score={job.get('match_score')}"))
    elif current_user.role == "employer":
        data = _employer_dashboard()
        sections = [
            ("Jobs", str(data["jobs_count"])),
            ("Applicants by status", str(data["applicants_by_status"])),
        ]
    else:
        data = _admin_dashboard()
        sections = [(k, str(v)) for k, v in data["counts"].items()]

    return document_pdf_response(
        "dashboard.pdf",
        f"Dashboard — {current_user.full_name}",
        sections,
    )
