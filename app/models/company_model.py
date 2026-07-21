from app.extensions import db
from app.utils import utc_now


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    industry = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    website = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    logo_url = db.Column(db.String(500), nullable=True)
    founded_year = db.Column(db.Integer, nullable=True)
    company_size = db.Column(db.String(50), nullable=True)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    owner = db.relationship("User", back_populates="company")
    jobs = db.relationship("Job", back_populates="company", cascade="all, delete-orphan")

    def to_dict(self, include_jobs=False, open_jobs_count=None):
        data = {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "industry": self.industry,
            "description": self.description,
            "website": self.website,
            "location": self.location,
            "logo_url": self.logo_url,
            "founded_year": self.founded_year,
            "company_size": self.company_size,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if open_jobs_count is not None:
            data["open_jobs_count"] = open_jobs_count
        if include_jobs:
            data["jobs"] = [j.to_dict() for j in self.jobs if j.status == "open"]
        return data
