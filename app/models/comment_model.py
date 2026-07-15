from app.extensions import db
from app.utils import utc_now


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    post = db.relationship("Post", back_populates="comments")
    author = db.relationship("User", back_populates="comments", foreign_keys=[author_id])

    def to_dict(self):
        return {
            "id": self.id,
            "post_id": self.post_id,
            "author_id": self.author_id,
            "body": self.body,
            "author": {
                "id": self.author.id,
                "full_name": self.author.full_name,
                "avatar_url": self.author.avatar_url,
            }
            if self.author
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
