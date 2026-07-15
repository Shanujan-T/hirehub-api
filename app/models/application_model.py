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

    job = db.relationship("Job", back_populates="applications")
    seeker = db.relationship("User", back_populates="applications", foreign_keys=[seeker_id])

    def to_dict(self, include_job=True, include_seeker=True):
        data = {
            "id": self.id,
            "job_id": self.job_id,
            "seeker_id": self.seeker_id,
            "cover_letter": self.cover_letter,
            "resume_url": self.resume_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_job and self.job:
            data["job"] = self.job.to_dict()
        if include_seeker and self.seeker:
            data["seeker"] = self.seeker.to_dict()
        return data
