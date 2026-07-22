from app.extensions import db
from app.utils import utc_now


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    passed = db.Column(db.Boolean, nullable=False, default=False)
    attempted_at = db.Column(db.DateTime, default=utc_now)

    user = db.relationship("User", backref="quiz_attempts")
    skill = db.relationship("Skill", backref="quiz_attempts")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "skill_id": self.skill_id,
            "score": self.score,
            "passed": self.passed,
            "attempted_at": self.attempted_at.isoformat() if self.attempted_at else None,
        }
