from app.extensions import db
from app.utils import utc_now


class PostBookmark(db.Model):
    __tablename__ = "post_bookmarks"
    __table_args__ = (db.UniqueConstraint("user_id", "post_id", name="uq_post_bookmark"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    user = db.relationship("User", foreign_keys=[user_id])
    post = db.relationship("Post", back_populates="bookmarks")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "post_id": self.post_id,
            "post": self.post.to_dict(include_author=True) if self.post else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
