from app.extensions import db
from app.utils import utc_now

REFERRAL_TYPES = ("internal_vacancy", "general_recommendation", "alumni_referral")
REFERRAL_STATUSES = ("pending", "submitted", "interviewing", "hired", "declined")


class JobReferral(db.Model):
    __tablename__ = "job_referrals"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    community_id = db.Column(db.Integer, db.ForeignKey("communities.id"), nullable=True)
    referral_type = db.Column(db.String(30), nullable=False, default="general_recommendation")
    candidate_name = db.Column(db.String(120), nullable=True)
    candidate_email = db.Column(db.String(120), nullable=True)
    candidate_resume_url = db.Column(db.String(500), nullable=True)
    vacancy_title = db.Column(db.String(200), nullable=True)
    vacancy_description = db.Column(db.Text, nullable=True)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    is_internal_vacancy = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    referrer = db.relationship("User", foreign_keys=[referrer_id])
    candidate = db.relationship("User", foreign_keys=[candidate_id])
    job = db.relationship("Job")
    company = db.relationship("Company")
    community = db.relationship("Community", back_populates="referrals")

    def to_dict(self):
        return {
            "id": self.id,
            "referrer_id": self.referrer_id,
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "company_id": self.company_id,
            "community_id": self.community_id,
            "referral_type": self.referral_type,
            "candidate_name": self.candidate_name,
            "candidate_email": self.candidate_email,
            "candidate_resume_url": self.candidate_resume_url,
            "vacancy_title": self.vacancy_title,
            "vacancy_description": self.vacancy_description,
            "message": self.message,
            "status": self.status,
            "is_internal_vacancy": self.is_internal_vacancy,
            "referrer": {
                "id": self.referrer.id,
                "full_name": self.referrer.full_name,
                "avatar_url": self.referrer.avatar_url,
            }
            if self.referrer
            else None,
            "candidate": self.candidate.to_dict() if self.candidate else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
