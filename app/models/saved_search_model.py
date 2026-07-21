from app.extensions import db
from app.utils import utc_now


class SavedSearch(db.Model):
    __tablename__ = "saved_searches"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    keywords = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    job_type = db.Column(db.String(20), nullable=True)
    min_salary = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    user = db.relationship("User", back_populates="saved_searches")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "keywords": self.keywords,
            "category": self.category,
            "location": self.location,
            "job_type": self.job_type,
            "min_salary": self.min_salary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
