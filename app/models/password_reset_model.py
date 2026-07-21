from datetime import timezone

from app.extensions import db
from app.utils import utc_now
from werkzeug.security import check_password_hash, generate_password_hash


def _normalize_dt(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class PasswordReset(db.Model):
    __tablename__ = "password_resets"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    user = db.relationship("User", back_populates="password_resets")

    def set_token(self, raw_token: str) -> None:
        self.token_hash = generate_password_hash(raw_token)

    def check_token(self, raw_token: str) -> bool:
        return check_password_hash(self.token_hash, raw_token)

    def is_valid(self) -> bool:
        if self.used_at is not None:
            return False
        return _normalize_dt(utc_now()) < _normalize_dt(self.expires_at)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
