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
