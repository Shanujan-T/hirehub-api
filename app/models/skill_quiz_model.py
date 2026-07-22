from app.extensions import db
from app.utils import utc_now


class SkillQuiz(db.Model):
    __tablename__ = "skill_quizzes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)
    correct_index = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    skill = db.relationship("Skill", backref="quiz_questions")

    def to_dict(self, include_answer=False):
        data = {
            "id": self.id,
            "skill_id": self.skill_id,
            "question": self.question,
            "options": self.options or [],
        }
        if include_answer:
            data["correct_index"] = self.correct_index
        return data

    def to_public_dict(self):
        return self.to_dict(include_answer=False)
