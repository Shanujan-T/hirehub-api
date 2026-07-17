import json

from app.extensions import db
from app.utils import utc_now

MENTORSHIP_FOCUS_AREAS = (
    "career_guidance",
    "resume_review",
    "interview_prep",
    "skill_development",
)


class MentorProfile(db.Model):
    __tablename__ = "mentor_profiles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    community_id = db.Column(db.Integer, db.ForeignKey("communities.id"), nullable=True)
    headline = db.Column(db.String(200), nullable=True)
    expertise_areas = db.Column(db.Text, nullable=True)
    years_experience = db.Column(db.Integer, nullable=True)
    available_for = db.Column(db.Text, nullable=True)
    max_mentees = db.Column(db.Integer, nullable=False, default=5)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    user = db.relationship("User", back_populates="mentor_profile")
    community = db.relationship("Community")

    def _parse_json_list(self, value):
        if not value:
            return []
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return [item.strip() for item in value.split(",") if item.strip()]

    def set_list_field(self, field_name, values):
        normalized = values if isinstance(values, list) else []
        setattr(self, field_name, json.dumps(normalized))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "community_id": self.community_id,
            "headline": self.headline,
            "expertise_areas": self._parse_json_list(self.expertise_areas),
            "years_experience": self.years_experience,
            "available_for": self._parse_json_list(self.available_for),
            "max_mentees": self.max_mentees,
            "is_available": self.is_available,
            "bio": self.bio,
            "user": {
                "id": self.user.id,
                "full_name": self.user.full_name,
                "avatar_url": self.user.avatar_url,
                "role": self.user.role,
                "location": self.user.location,
            }
            if self.user
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
