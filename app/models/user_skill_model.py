from app.extensions import db
from app.utils import utc_now

SKILL_LEVELS = ("beginner", "intermediate", "advanced", "expert")


class UserSkill(db.Model):
    __tablename__ = "user_skills"
    __table_args__ = (db.UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    level = db.Column(db.String(20), nullable=False, default="beginner")
    created_at = db.Column(db.DateTime, default=utc_now)
