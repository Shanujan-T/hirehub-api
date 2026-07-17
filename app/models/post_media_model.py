from app.extensions import db
from app.utils import utc_now

MEDIA_TYPES = ("image", "pdf", "video")


class PostMedia(db.Model):
    __tablename__ = "post_media"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    post = db.relationship("Post", back_populates="media")

    def to_dict(self):
        return {
            "id": self.id,
            "post_id": self.post_id,
            "media_type": self.media_type,
            "url": self.url,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
