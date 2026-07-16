from app.extensions import db
from app.utils import utc_now


class CommunityAnnouncement(db.Model):
    __tablename__ = "community_announcements"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    community_id = db.Column(db.Integer, db.ForeignKey("communities.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    community = db.relationship("Community", back_populates="announcements")
    author = db.relationship("User", foreign_keys=[author_id])

    def to_dict(self):
        return {
            "id": self.id,
            "community_id": self.community_id,
            "author_id": self.author_id,
            "title": self.title,
            "body": self.body,
            "is_pinned": self.is_pinned,
            "author": {
                "id": self.author.id,
                "full_name": self.author.full_name,
                "avatar_url": self.author.avatar_url,
            }
            if self.author
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
