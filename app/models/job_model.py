from app.extensions import db
from app.utils import utc_now

JOB_TYPES = ("full_time", "part_time", "internship", "contract")
EXPERIENCE_LEVELS = ("entry", "junior", "mid", "senior")
JOB_STATUSES = ("open", "closed", "filled")


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    posted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    job_type = db.Column(db.String(20), nullable=False, default="full_time")
    experience_level = db.Column(db.String(20), nullable=False, default="entry")
    location = db.Column(db.String(120), nullable=True)
    salary_min = db.Column(db.Integer, nullable=True)
    salary_max = db.Column(db.Integer, nullable=True)
    deadline = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="open")
    image_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    company = db.relationship("Company", back_populates="jobs")
    poster = db.relationship("User", back_populates="posted_jobs", foreign_keys=[posted_by])
    job_skills = db.relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    applications = db.relationship("Application", back_populates="job", cascade="all, delete-orphan")
    saved_by = db.relationship("SavedJob", back_populates="job", cascade="all, delete-orphan")

    def to_dict(self, include_skills=True, include_company=True):
        data = {
            "id": self.id,
            "company_id": self.company_id,
            "posted_by": self.posted_by,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "job_type": self.job_type,
            "experience_level": self.experience_level,
            "location": self.location,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "status": self.status,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_company and self.company:
            data["company"] = self.company.to_dict()
        if include_skills:
            data["skills"] = [js.to_dict() for js in self.job_skills]
            data["skill_ids"] = [js.skill_id for js in self.job_skills]
        return data
