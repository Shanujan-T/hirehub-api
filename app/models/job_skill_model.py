from app.extensions import db
from app.utils import utc_now


class JobSkill(db.Model):
    __tablename__ = "job_skills"
    __table_args__ = (db.UniqueConstraint("job_id", "skill_id", name="uq_job_skill"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    job = db.relationship("Job", back_populates="job_skills")
    skill = db.relationship("Skill", back_populates="job_skills")

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "skill_id": self.skill_id,
            "skill": self.skill.to_dict() if self.skill else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
