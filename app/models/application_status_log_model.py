from app.extensions import db
from app.models.application_model import APPLICATION_STATUSES
from app.utils import utc_now


class ApplicationStatusLog(db.Model):
    __tablename__ = "application_status_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False)
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    application = db.relationship("Application", backref="status_logs")
    changer = db.relationship("User", foreign_keys=[changed_by])

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "changed_by": self.changed_by,
            "changed_by_name": self.changer.full_name if self.changer else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
