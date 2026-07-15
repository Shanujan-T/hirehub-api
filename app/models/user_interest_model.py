from app.extensions import db
from app.utils import utc_now


class UserInterest(db.Model):
    __tablename__ = "user_interests"
    __table_args__ = (db.UniqueConstraint("user_id", "interest_id", name="uq_user_interest"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    interest_id = db.Column(db.Integer, db.ForeignKey("interests.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    user = db.relationship("User", back_populates="interests")
    interest = db.relationship("Interest", back_populates="user_interests")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "interest_id": self.interest_id,
            "interest": self.interest.to_dict() if self.interest else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
