from app.extensions import db
from app.utils import utc_now


class SavedJob(db.Model):
    __tablename__ = "saved_jobs"
    __table_args__ = (db.UniqueConstraint("seeker_id", "job_id", name="uq_saved_job"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    seeker_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
