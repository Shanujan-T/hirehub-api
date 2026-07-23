from app.extensions import db
from app.utils import utc_now


class Conversation(db.Model):
    __tablename__ = "conversations"
    __table_args__ = (db.UniqueConstraint("application_id", name="uq_conversation_application"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False)
    employer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    seeker_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    application = db.relationship("Application", backref="conversation")
    employer = db.relationship("User", foreign_keys=[employer_id])
    seeker = db.relationship("User", foreign_keys=[seeker_id])
    messages = db.relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at.asc()",
    )

    def to_dict(self, include_participants=False, include_application=False):
        data = {
            "id": self.id,
            "application_id": self.application_id,
            "employer_id": self.employer_id,
            "seeker_id": self.seeker_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_participants:
            data["employer"] = self.employer.to_dict() if self.employer else None
            data["seeker"] = self.seeker.to_dict() if self.seeker else None
        if include_application and self.application:
            data["application"] = self.application.to_dict(include_job=True)
        return data
