from app.extensions import db
from app.utils import utc_now


class Interest(db.Model):
    __tablename__ = "interests"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
