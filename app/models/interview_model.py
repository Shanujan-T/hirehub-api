from app.extensions import db
from app.utils import utc_now

INTERVIEW_STATUSES = ("proposed", "confirmed", "cancelled")


class Interview(db.Model):
    __tablename__ = "interviews"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    application_id = db.Column(
        db.Integer, db.ForeignKey("applications.id"), nullable=False, index=True
    )
    proposed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    slots = db.Column(db.JSON, nullable=False)
    selected_slot = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="proposed")
    created_at = db.Column(db.DateTime, default=utc_now)

    application = db.relationship("Application", back_populates="interviews")
    proposer = db.relationship("User", foreign_keys=[proposed_by])

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "proposed_by": self.proposed_by,
            "slots": self.slots or [],
            "selected_slot": self.selected_slot.isoformat() if self.selected_slot else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
