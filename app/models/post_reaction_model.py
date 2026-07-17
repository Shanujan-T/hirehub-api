from app.extensions import db
from app.utils import utc_now

REACTION_TYPES = ("like", "love", "celebrate", "insightful", "support")


class PostReaction(db.Model):
    __tablename__ = "post_reactions"
    __table_args__ = (db.UniqueConstraint("post_id", "user_id", name="uq_post_reaction"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False, default="like")
    created_at = db.Column(db.DateTime, default=utc_now)

    post = db.relationship("Post", back_populates="reactions")
    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "reaction_type": self.reaction_type,
            "user": {
                "id": self.user.id,
                "full_name": self.user.full_name,
                "avatar_url": self.user.avatar_url,
            }
            if self.user
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
