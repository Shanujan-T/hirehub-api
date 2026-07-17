from app.extensions import db
from app.utils import utc_now

post_hashtags = db.Table(
    "post_hashtags",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id"), primary_key=True),
    db.Column("hashtag_id", db.Integer, db.ForeignKey("hashtags.id"), primary_key=True),
)


class Hashtag(db.Model):
    __tablename__ = "hashtags"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    posts = db.relationship("Post", secondary=post_hashtags, back_populates="hashtags")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
