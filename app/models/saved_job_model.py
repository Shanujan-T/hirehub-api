from app.extensions import db
from app.utils import utc_now


class SavedJob(db.Model):
    __tablename__ = "saved_jobs"
    __table_args__ = (db.UniqueConstraint("seeker_id", "job_id", name="uq_saved_job"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    seeker_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    seeker = db.relationship("User", foreign_keys=[seeker_id])
    job = db.relationship("Job", back_populates="saved_by")

    def to_dict(self):
        return {
            "id": self.id,
            "seeker_id": self.seeker_id,
            "job_id": self.job_id,
            "job": self.job.to_dict() if self.job else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
