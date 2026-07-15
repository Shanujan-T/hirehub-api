from app.extensions import db
from app.utils import utc_now


class UserInterest(db.Model):
    __tablename__ = "user_interests"
    __table_args__ = (db.UniqueConstraint("user_id", "interest_id", name="uq_user_interest"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    interest_id = db.Column(db.Integer, db.ForeignKey("interests.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
