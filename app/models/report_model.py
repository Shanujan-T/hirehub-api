from app.extensions import db
from app.utils import utc_now

REPORT_TARGET_TYPES = (
    "post",
    "comment",
    "job",
    "user",
    "community",
    "referral",
    "conversation",
    "message",
)
REPORT_STATUSES = ("open", "reviewed", "dismissed", "actioned")


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    target_type = db.Column(db.String(20), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="open")
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    reporter = db.relationship("User", back_populates="reports_filed", foreign_keys=[reporter_id])
    resolver = db.relationship("User", foreign_keys=[resolved_by])

    def to_dict(self):
        return {
            "id": self.id,
            "reporter_id": self.reporter_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "reason": self.reason,
            "details": self.details,
            "status": self.status,
            "resolved_by": self.resolved_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
