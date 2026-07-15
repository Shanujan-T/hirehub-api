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
