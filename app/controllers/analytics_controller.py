from collections import defaultdict

from flask import jsonify
from sqlalchemy import func

from app.extensions import db
from app.models import Application, Job, JobSkill, Skill, User


def get_admin_analytics():
    jobs_by_category = (
        db.session.query(Job.category, func.count(Job.id))
        .filter(Job.category.isnot(None), Job.category != "")
        .group_by(Job.category)
        .order_by(func.count(Job.id).desc())
        .all()
    )

    apps = Application.query.order_by(Application.created_at.asc()).all()
    week_counts = defaultdict(int)
    status_counts = defaultdict(int)
    for app_row in apps:
        status_counts[app_row.status] += 1
        if app_row.created_at:
            week_key = app_row.created_at.strftime("%G-W%V")
            week_counts[week_key] += 1

    top_skills = (
        db.session.query(Skill.name, func.count(JobSkill.id))
        .join(JobSkill, JobSkill.skill_id == Skill.id)
        .join(Job, Job.id == JobSkill.job_id)
        .filter(Job.status == "open")
        .group_by(Skill.name)
        .order_by(func.count(JobSkill.id).desc())
        .limit(10)
        .all()
    )

    return jsonify({
        "jobs_by_category": [
            {"category": cat or "Uncategorized", "count": count}
            for cat, count in jobs_by_category
        ],
        "applications_by_week": [
            {"week": week, "count": count}
            for week, count in sorted(week_counts.items())
        ],
        "top_skills_in_demand": [
            {"skill": name, "count": count} for name, count in top_skills
        ],
        "applications_by_status": [
            {"status": status, "count": count}
            for status, count in sorted(status_counts.items())
        ],
        "total_users": User.query.count(),
        "total_jobs": Job.query.count(),
        "total_applications": Application.query.count(),
    }), 200
