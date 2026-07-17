from app.extensions import db
from app.utils import utc_now

SESSION_STATUSES = ("scheduled", "completed", "cancelled")


class MentorshipSession(db.Model):
    __tablename__ = "mentorship_sessions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mentorship_id = db.Column(db.Integer, db.ForeignKey("mentorships.id"), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    focus_area = db.Column(db.String(30), nullable=True)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="scheduled")
    created_at = db.Column(db.DateTime, default=utc_now)

    mentorship = db.relationship("Mentorship", back_populates="sessions")

    def to_dict(self):
        return {
            "id": self.id,
            "mentorship_id": self.mentorship_id,
            "topic": self.topic,
            "focus_area": self.focus_area,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
