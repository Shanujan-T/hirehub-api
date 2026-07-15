from app.extensions import db
from app.utils import utc_now


class Conversation(db.Model):
    __tablename__ = "conversations"
    __table_args__ = (
        db.UniqueConstraint("participant_one_id", "participant_two_id", name="uq_conversation_pair"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    participant_one_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    participant_two_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    participant_one = db.relationship("User", foreign_keys=[participant_one_id])
    participant_two = db.relationship("User", foreign_keys=[participant_two_id])
    messages = db.relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "participant_one_id": self.participant_one_id,
            "participant_two_id": self.participant_two_id,
            "participant_one": self.participant_one.to_dict() if self.participant_one else None,
            "participant_two": self.participant_two.to_dict() if self.participant_two else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
