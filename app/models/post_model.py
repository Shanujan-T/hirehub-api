from app.extensions import db
from app.utils import utc_now

POST_TYPES = (
    "discussion",
    "job_opportunity",
    "internship",
    "career_advice",
    "interview_experience",
    "success_story",
    "hiring_announcement",
    "referral_request",
    "learning_resource",
    "event",
    "workshop",
    "job_share",
    "guidance",
    "announcement",
)


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey("communities.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(30), nullable=False, default="discussion")
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=True)
    link_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    author = db.relationship("User", back_populates="posts", foreign_keys=[author_id])
    community = db.relationship("Community", back_populates="posts")
    job = db.relationship("Job")
    comments = db.relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    media = db.relationship("PostMedia", back_populates="post", cascade="all, delete-orphan")
    hashtags = db.relationship("Hashtag", secondary="post_hashtags", back_populates="posts")
    reactions = db.relationship("PostReaction", back_populates="post", cascade="all, delete-orphan")
    bookmarks = db.relationship("PostBookmark", back_populates="post", cascade="all, delete-orphan")
    mentions = db.relationship("PostMention", back_populates="post", cascade="all, delete-orphan")

    def to_dict(self, include_author=True, include_comments=False, include_details=False):
        data = {
            "id": self.id,
            "author_id": self.author_id,
            "community_id": self.community_id,
            "title": self.title,
            "body": self.body,
            "type": self.type,
            "job_id": self.job_id,
            "link_url": self.link_url,
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
            top_level = [c for c in self.comments if c.parent_id is None]
            data["comments"] = [c.to_dict(include_replies=True) for c in top_level]
        if include_details:
            data["media"] = [m.to_dict() for m in self.media]
            data["hashtags"] = [h.to_dict() for h in self.hashtags]
            data["mentions"] = [m.to_dict() for m in self.mentions]
            data["reaction_count"] = len(self.reactions)
            data["reactions_summary"] = self._reactions_summary()
        return data

    def _reactions_summary(self):
        summary = {}
        for reaction in self.reactions:
            summary[reaction.reaction_type] = summary.get(reaction.reaction_type, 0) + 1
        return summary
