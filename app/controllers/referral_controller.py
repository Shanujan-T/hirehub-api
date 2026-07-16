from flask import jsonify, request
from flask_jwt_extended import current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Community, Company, Job, JobReferral, User
from app.models.job_referral_model import REFERRAL_STATUSES, REFERRAL_TYPES
from app.utils.social_helpers import get_membership, is_community_member, notify


def create_referral():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    referral_type = str(data.get("referral_type") or "general_recommendation").strip().lower()
    if referral_type not in REFERRAL_TYPES:
        return jsonify({"errors": [f"referral_type must be one of: {', '.join(REFERRAL_TYPES)}."]}), 400

    community_id = data.get("community_id")
    if community_id:
        community = db.session.get(Community, community_id)
        if not community:
            return jsonify({"errors": ["community_id not found."]}), 400
        membership = get_membership(current_user.id, community.id)
        if not is_community_member(membership):
            return jsonify({"error": "Join the community before creating referrals."}), 403

    candidate_id = data.get("candidate_id")
    candidate = None
    if candidate_id:
        candidate = db.session.get(User, candidate_id)
        if not candidate:
            return jsonify({"errors": ["candidate_id not found."]}), 400

    job_id = data.get("job_id")
    if job_id and not db.session.get(Job, job_id):
        return jsonify({"errors": ["job_id not found."]}), 400

    company_id = data.get("company_id")
    if company_id and not db.session.get(Company, company_id):
        return jsonify({"errors": ["company_id not found."]}), 400

    candidate_name = data.get("candidate_name") or (candidate.full_name if candidate else None)
    if not candidate_name and not candidate_id:
        return jsonify({"errors": ["candidate_name or candidate_id is required."]}), 400

    try:
        row = JobReferral(
            referrer_id=current_user.id,
            candidate_id=candidate.id if candidate else None,
            job_id=job_id,
            company_id=company_id,
            community_id=community_id,
            referral_type=referral_type,
            candidate_name=candidate_name,
            candidate_email=data.get("candidate_email") or (candidate.email if candidate else None),
            candidate_resume_url=data.get("candidate_resume_url")
            or (candidate.resume_url if candidate else None),
            vacancy_title=data.get("vacancy_title"),
            vacancy_description=data.get("vacancy_description"),
            message=data.get("message"),
            is_internal_vacancy=bool(data.get("is_internal_vacancy", referral_type == "internal_vacancy")),
            status="pending",
        )
        db.session.add(row)
        db.session.flush()
        if candidate:
            notify(
                candidate.id,
                "job_referral",
                f"{current_user.full_name} referred you for an opportunity.",
                f"/referrals/{row.id}",
            )
        db.session.commit()
        return jsonify({"message": "Referral created.", "referral": row.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def get_referrals():
    community_id = request.args.get("community_id")
    job_id = request.args.get("job_id")
    query = JobReferral.query

    if community_id:
        query = query.filter_by(community_id=int(community_id))
    if job_id:
        query = query.filter_by(job_id=int(job_id))

    if current_user.role == "admin":
        rows = query.order_by(JobReferral.id.desc()).all()
    else:
        rows = query.filter(
            or_(
                JobReferral.referrer_id == current_user.id,
                JobReferral.candidate_id == current_user.id,
            )
        ).order_by(JobReferral.id.desc()).all()

    return jsonify({"referrals": [r.to_dict() for r in rows]}), 200


def get_my_referrals():
    rows = JobReferral.query.filter_by(referrer_id=current_user.id).order_by(
        JobReferral.id.desc()
    ).all()
    return jsonify({"referrals": [r.to_dict() for r in rows]}), 200


def get_referral(referral_id):
    row = db.session.get(JobReferral, referral_id)
    if not row:
        return jsonify({"error": "Referral not found."}), 404
    if (
        current_user.role != "admin"
        and current_user.id not in (row.referrer_id, row.candidate_id)
    ):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403
    return jsonify({"referral": row.to_dict()}), 200


def update_referral_status(referral_id):
    row = db.session.get(JobReferral, referral_id)
    if not row:
        return jsonify({"error": "Referral not found."}), 404
    if current_user.id not in (row.referrer_id, row.candidate_id) and current_user.role != "admin":
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    data = request.get_json(silent=True) or {}
    status = str(data.get("status") or "").strip().lower()
    if status not in REFERRAL_STATUSES:
        return jsonify({"errors": [f"status must be one of: {', '.join(REFERRAL_STATUSES)}."]}), 400

    try:
        row.status = status
        if row.referrer_id != current_user.id:
            notify(
                row.referrer_id,
                "referral_status",
                f"Referral status updated to {status}.",
                f"/referrals/{row.id}",
            )
        db.session.commit()
        return jsonify({"message": "Referral updated.", "referral": row.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
