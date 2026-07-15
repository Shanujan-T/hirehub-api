from app.extensions import db
from app.utils import utc_now

MENTORSHIP_STATUSES = ("requested", "active", "ended", "declined")


class Mentorship(db.Model):
    __tablename__ = "mentorships"
    __table_args__ = (db.UniqueConstraint("mentor_id", "mentee_id", name="uq_mentorship"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    mentee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="requested")
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    mentor = db.relationship("User", foreign_keys=[mentor_id])
    mentee = db.relationship("User", foreign_keys=[mentee_id])

    def to_dict(self):
        return {
            "id": self.id,
            "mentor_id": self.mentor_id,
            "mentee_id": self.mentee_id,
            "status": self.status,
            "message": self.message,
            "mentor": self.mentor.to_dict() if self.mentor else None,
            "mentee": self.mentee.to_dict() if self.mentee else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
