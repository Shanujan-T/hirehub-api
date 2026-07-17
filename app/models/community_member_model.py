from app.extensions import db
from app.utils import utc_now

COMMUNITY_ROLES = ("admin", "moderator", "member")


class CommunityMember(db.Model):
    __tablename__ = "community_members"
    __table_args__ = (db.UniqueConstraint("community_id", "user_id", name="uq_community_member"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    community_id = db.Column(db.Integer, db.ForeignKey("communities.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")
    joined_at = db.Column(db.DateTime, default=utc_now)

    community = db.relationship("Community", back_populates="members")
    user = db.relationship("User", back_populates="community_memberships")

    def to_dict(self):
        return {
            "id": self.id,
            "community_id": self.community_id,
            "user_id": self.user_id,
            "role": self.role,
            "user": {
                "id": self.user.id,
                "full_name": self.user.full_name,
                "avatar_url": self.user.avatar_url,
                "role": self.user.role,
            }
            if self.user
            else None,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }
