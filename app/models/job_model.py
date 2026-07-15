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
    created_at = db.Column(db.DateTime, default=utc_now)
