from app.extensions import db
from app.utils import utc_now


class PostMention(db.Model):
    __tablename__ = "post_mentions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey("comments.id"), nullable=True)
    mentioned_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    post = db.relationship("Post", back_populates="mentions")
    comment = db.relationship("Comment", back_populates="mentions")
    mentioned_user = db.relationship("User", foreign_keys=[mentioned_user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "post_id": self.post_id,
            "comment_id": self.comment_id,
            "mentioned_user_id": self.mentioned_user_id,
            "mentioned_user": {
                "id": self.mentioned_user.id,
                "full_name": self.mentioned_user.full_name,
                "avatar_url": self.mentioned_user.avatar_url,
            }
            if self.mentioned_user
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
