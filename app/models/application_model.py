from app.extensions import db
from app.utils import utc_now

APPLICATION_STATUSES = ("pending", "shortlisted", "accepted", "rejected", "withdrawn")


class Application(db.Model):
    __tablename__ = "applications"
    __table_args__ = (db.UniqueConstraint("job_id", "seeker_id", name="uq_job_seeker"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    seeker_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    cover_letter = db.Column(db.Text, nullable=True)
    resume_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, default=utc_now)
