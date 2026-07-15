from app.extensions import db
from app.utils import utc_now

POST_TYPES = ("discussion", "job_share", "success_story", "guidance")


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(30), nullable=False, default="discussion")
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    author = db.relationship("User", back_populates="posts", foreign_keys=[author_id])
    job = db.relationship("Job")
    comments = db.relationship("Comment", back_populates="post", cascade="all, delete-orphan")

    def to_dict(self, include_author=True, include_comments=False):
        data = {
            "id": self.id,
            "author_id": self.author_id,
            "title": self.title,
            "body": self.body,
            "type": self.type,
            "job_id": self.job_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_author and self.author:
            data["author"] = {
                "id": self.author.id,
                "full_name": self.author.full_name,
                "role": self.author.role,
                "avatar_url": self.author.avatar_url,
            }
        if include_comments:
            data["comments"] = [c.to_dict() for c in self.comments]
        return data
