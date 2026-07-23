from app.extensions import db
from app.utils import utc_now
from werkzeug.security import check_password_hash, generate_password_hash

VALID_ROLES = ("seeker", "employer", "admin")
PUBLIC_REGISTER_ROLES = ("seeker", "employer")
EDUCATION_LEVELS = ("school", "diploma", "bachelors", "masters", "other")
NOTIFY_VIA_OPTIONS = ("email", "whatsapp", "both", "none")


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
    whatsapp_number = db.Column(db.String(40), nullable=True)
    notify_via = db.Column(db.String(20), nullable=True, default="email")
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    education_level = db.Column(db.String(20), nullable=True)
    resume_url = db.Column(db.String(500), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_active_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    skills = db.relationship(
        "UserSkill",
        back_populates="user",
        foreign_keys="UserSkill.user_id",
        cascade="all, delete-orphan",
    )
    interests = db.relationship("UserInterest", back_populates="user", cascade="all, delete-orphan")
    company = db.relationship("Company", back_populates="owner", uselist=False)
    posted_jobs = db.relationship("Job", back_populates="poster", foreign_keys="Job.posted_by")
    applications = db.relationship("Application", back_populates="seeker", foreign_keys="Application.seeker_id")
    posts = db.relationship("Post", back_populates="author", foreign_keys="Post.author_id")
    comments = db.relationship("Comment", back_populates="author", foreign_keys="Comment.author_id")
    reports_filed = db.relationship("Report", back_populates="reporter", foreign_keys="Report.reporter_id")
    community_memberships = db.relationship("CommunityMember", back_populates="user")
    mentor_profile = db.relationship("MentorProfile", back_populates="user", uselist=False)
    password_resets = db.relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")
    saved_searches = db.relationship("SavedSearch", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self, include_skills=False):
        data = {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "full_name": self.full_name,
            "bio": self.bio,
            "location": self.location,
            "phone": self.phone,
            "whatsapp_number": self.whatsapp_number,
            "notify_via": self.notify_via or "email",
            "latitude": self.latitude,
            "longitude": self.longitude,
            "education_level": self.education_level,
            "resume_url": self.resume_url,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_skills:
            data["skills"] = [us.to_dict() for us in self.skills]
            data["interests"] = [ui.to_dict() for ui in self.interests]
        return data
