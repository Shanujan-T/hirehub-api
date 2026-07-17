import re

from app.extensions import db
from app.utils import utc_now

COMMUNITY_TYPES = (
    "organization",
    "university",
    "profession",
    "industry",
    "location",
    "interest",
)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
    return slug.strip("-") or "community"


class Community(db.Model):
    __tablename__ = "communities"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(160), nullable=False, unique=True)
    type = db.Column(db.String(30), nullable=False, default="organization")
    description = db.Column(db.Text, nullable=True)
    rules = db.Column(db.Text, nullable=True)
    cover_image_url = db.Column(db.String(500), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    industry = db.Column(db.String(120), nullable=True)
    is_public = db.Column(db.Boolean, nullable=False, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    creator = db.relationship("User", foreign_keys=[created_by])
    members = db.relationship(
        "CommunityMember", back_populates="community", cascade="all, delete-orphan"
    )
    posts = db.relationship("Post", back_populates="community")
    announcements = db.relationship(
        "CommunityAnnouncement", back_populates="community", cascade="all, delete-orphan"
    )
    referrals = db.relationship("JobReferral", back_populates="community")

    def to_dict(self, include_member_count=False):
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "type": self.type,
            "description": self.description,
            "rules": self.rules,
            "cover_image_url": self.cover_image_url,
            "avatar_url": self.avatar_url,
            "location": self.location,
            "industry": self.industry,
            "is_public": self.is_public,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_member_count:
            data["member_count"] = len(self.members)
        return data

    @staticmethod
    def make_unique_slug(name: str) -> str:
        base = _slugify(name)
        slug = base
        counter = 1
        while Community.query.filter_by(slug=slug).first():
            slug = f"{base}-{counter}"
            counter += 1
        return slug
