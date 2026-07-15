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
