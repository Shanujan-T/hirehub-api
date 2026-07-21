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
    verified = db.Column(db.Boolean, nullable=False, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    user = db.relationship("User", back_populates="skills", foreign_keys=[user_id])
    skill = db.relationship("Skill", back_populates="user_skills")
    verifier = db.relationship("User", foreign_keys=[verified_by], viewonly=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "skill_id": self.skill_id,
            "level": self.level,
            "verified": self.verified,
            "verified_by": self.verified_by,
            "skill": self.skill.to_dict() if self.skill else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
