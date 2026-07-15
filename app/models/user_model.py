from app.extensions import db
from app.utils import utc_now
from werkzeug.security import check_password_hash, generate_password_hash

VALID_ROLES = ("seeker", "employer", "admin")
PUBLIC_REGISTER_ROLES = ("seeker", "employer")
EDUCATION_LEVELS = ("school", "diploma", "bachelors", "masters", "other")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="seeker")
    full_name = db.Column(db.String(120), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(40), nullable=True)
    education_level = db.Column(db.String(20), nullable=True)
    resume_url = db.Column(db.String(500), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)
