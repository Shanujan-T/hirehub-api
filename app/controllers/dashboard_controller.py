from collections import Counter

from flask import jsonify
from flask_jwt_extended import current_user

from app.models import (
    Application,
    ApplicationStatusLog,
    CommunityMember,
    Company,
    Job,
    Post,
    Report,
    SavedJob,
    User,
    UserSkill,
)
from app.utils.pdf_utils import document_pdf_response
from app.utils.profile_completion import compute_profile_completion


def _seeker_dashboard():
    apps = Application.query.filter_by(seeker_id=current_user.id).all()
    by_status = Counter(a.status for a in apps)
    # Reuse recommendation logic without returning a Response
    from app.models import Job as JobModel

    user_skills = UserSkill.query.filter_by(user_id=current_user.id).all()
    user_skill_ids = {us.skill_id for us in user_skills}
    skill_names = {us.skill_id: us.skill.name for us in user_skills if us.skill}
    recommended = []
    for job in JobModel.query.filter_by(status="open").all():
        job_skill_ids = {js.skill_id for js in job.job_skills}
        overlap_ids = user_skill_ids & job_skill_ids
        overlap = len(overlap_ids)
        boost = 0
        if (
            current_user.location
            and job.location
            and current_user.location.strip().lower() == job.location.strip().lower()
        ):
            boost = 2
        score = overlap * 3 + boost
        if score > 0:
            matched_skills = [skill_names[sid] for sid in overlap_ids if sid in skill_names]
            recommended.append((score, job, matched_skills))
    recommended.sort(key=lambda x: (-x[0], -x[1].id))

    apps_count = len(apps)
    community_count = CommunityMember.query.filter_by(user_id=current_user.id).count()
    completion_score, badges, onboarding_checklist = compute_profile_completion(
        current_user,
        skills=user_skills,
        applications_count=apps_count,
        community_count=community_count,
    )

    return {
        "role": "seeker",
        "applications_by_status": dict(by_status),
        "applications": [a.to_dict() for a in apps[:20]],
        "recommended_jobs": [
            {**j.to_dict(), "match_score": s, "matched_skills": matched}
            for s, j, matched in recommended[:10]
        ],
        "profile_completion_score": completion_score,
        "badges": badges,
        "onboarding_checklist": onboarding_checklist,
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


def get_seeker_stats():
    if current_user.role != "seeker":
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    applications_sent = Application.query.filter_by(seeker_id=current_user.id).count()
    jobs_saved = SavedJob.query.filter_by(seeker_id=current_user.id).count()
    communities_joined = CommunityMember.query.filter_by(user_id=current_user.id).count()

    return jsonify({
        "stats": {
            "applications_sent": applications_sent,
            "jobs_saved": jobs_saved,
            "communities_joined": communities_joined,
        }
    }), 200


def _activity_description(log, application):
    job_title = application.job.title if application.job else "a job"
    if log.old_status is None:
        return f"Application submitted for {job_title}"
    if log.new_status.startswith("interview_"):
        label = log.new_status.replace("_", " ")
        return f"Interview update for {job_title}: {label}"
    return f"Application for {job_title} changed to {log.new_status.replace('_', ' ')}"


def get_seeker_activity():
    if current_user.role != "seeker":
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    logs = (
        ApplicationStatusLog.query.join(Application)
        .filter(Application.seeker_id == current_user.id)
        .order_by(ApplicationStatusLog.created_at.desc())
        .limit(5)
        .all()
    )

    activity = []
    for log in logs:
        app_row = log.application
        activity.append({
            "id": log.id,
            "type": "application_status",
            "description": _activity_description(log, app_row),
            "application_id": log.application_id,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return jsonify({"activity": activity}), 200
