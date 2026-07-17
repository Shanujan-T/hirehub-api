from flask import jsonify, request
from flask_jwt_extended import current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Community, CommunityAnnouncement, CommunityMember, Post
from app.models.community_model import COMMUNITY_TYPES
from app.models.community_member_model import COMMUNITY_ROLES
from app.utils.social_helpers import (
    can_manage_community,
    can_moderate_community,
    get_membership,
    is_community_member,
    notify,
)


def get_communities():
    q = (request.args.get("q") or "").strip()
    community_type = (request.args.get("type") or "").strip().lower()
    location = (request.args.get("location") or "").strip()

    query = Community.query
    if q:
        query = query.filter(
            or_(Community.name.ilike(f"%{q}%"), Community.description.ilike(f"%{q}%"))
        )
    if community_type:
        query = query.filter(Community.type == community_type)
    if location:
        query = query.filter(Community.location.ilike(f"%{location}%"))

    rows = query.order_by(Community.id.desc()).all()
    return jsonify({"communities": [c.to_dict(include_member_count=True) for c in rows]}), 200


def create_community():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    name = str(data.get("name") or "").strip()
    community_type = str(data.get("type") or "organization").strip().lower()
    errors = []
    if not name:
        errors.append("name is required.")
    if community_type not in COMMUNITY_TYPES:
        errors.append(f"type must be one of: {', '.join(COMMUNITY_TYPES)}.")
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        community = Community(
            name=name,
            slug=Community.make_unique_slug(name),
            type=community_type,
            description=data.get("description"),
            rules=data.get("rules"),
            cover_image_url=data.get("cover_image_url"),
            avatar_url=data.get("avatar_url"),
            location=data.get("location"),
            industry=data.get("industry"),
            is_public=bool(data.get("is_public", True)),
            created_by=current_user.id,
        )
        db.session.add(community)
        db.session.flush()
        db.session.add(
            CommunityMember(
                community_id=community.id,
                user_id=current_user.id,
                role="admin",
            )
        )
        db.session.commit()
        return jsonify({"message": "Community created.", "community": community.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def get_community(community_id):
    community = db.session.get(Community, community_id)
    if not community:
        return jsonify({"error": "Community not found."}), 404
    return jsonify({"community": community.to_dict(include_member_count=True)}), 200


def update_community(community_id):
    community = db.session.get(Community, community_id)
    if not community:
        return jsonify({"error": "Community not found."}), 404

    membership = get_membership(current_user.id, community.id)
    if not can_manage_community(membership, current_user):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    try:
        if "name" in data:
            name = str(data.get("name") or "").strip()
            if not name:
                return jsonify({"errors": ["name cannot be empty."]}), 400
            community.name = name
        for field in (
            "description",
            "rules",
            "cover_image_url",
            "avatar_url",
            "location",
            "industry",
        ):
            if field in data:
                setattr(community, field, data.get(field))
        if "type" in data:
            community_type = str(data.get("type")).strip().lower()
            if community_type not in COMMUNITY_TYPES:
                return jsonify({"errors": [f"type must be one of: {', '.join(COMMUNITY_TYPES)}."]}), 400
            community.type = community_type
        if "is_public" in data:
            community.is_public = bool(data.get("is_public"))
        db.session.commit()
        return jsonify({"message": "Community updated.", "community": community.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def delete_community(community_id):
    community = db.session.get(Community, community_id)
    if not community:
        return jsonify({"error": "Community not found."}), 404

    membership = get_membership(current_user.id, community.id)
    if not can_manage_community(membership, current_user) and community.created_by != current_user.id:
        if current_user.role != "admin":
            return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    try:
        db.session.delete(community)
        db.session.commit()
        return jsonify({"message": "Community deleted."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def join_community(community_id):
    community = db.session.get(Community, community_id)
    if not community:
        return jsonify({"error": "Community not found."}), 404
    if get_membership(current_user.id, community.id):
        return jsonify({"error": "Already a member of this community."}), 400
    try:
        row = CommunityMember(
            community_id=community.id,
            user_id=current_user.id,
            role="member",
        )
        db.session.add(row)
        db.session.commit()
        return jsonify({"message": "Joined community.", "membership": row.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def leave_community(community_id):
    membership = get_membership(current_user.id, community_id)
    if not membership:
        return jsonify({"error": "Not a member of this community."}), 404
    if membership.role == "admin":
        admin_count = CommunityMember.query.filter_by(
            community_id=community_id, role="admin"
        ).count()
        if admin_count <= 1:
            return jsonify({"error": "Assign another admin before leaving."}), 400
    try:
        db.session.delete(membership)
        db.session.commit()
        return jsonify({"message": "Left community."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def get_community_members(community_id):
    community = db.session.get(Community, community_id)
    if not community:
        return jsonify({"error": "Community not found."}), 404
    rows = CommunityMember.query.filter_by(community_id=community.id).order_by(
        CommunityMember.id.asc()
    ).all()
    return jsonify({"members": [r.to_dict() for r in rows]}), 200


def update_member_role(community_id, user_id):
    community = db.session.get(Community, community_id)
    if not community:
        return jsonify({"error": "Community not found."}), 404

    actor = get_membership(current_user.id, community.id)
    if not can_manage_community(actor, current_user):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    target = get_membership(user_id, community.id)
    if not target:
        return jsonify({"error": "Member not found."}), 404

    data = request.get_json(silent=True) or {}
    role = str(data.get("role") or "").strip().lower()
    if role not in COMMUNITY_ROLES:
        return jsonify({"errors": [f"role must be one of: {', '.join(COMMUNITY_ROLES)}."]}), 400

    try:
        target.role = role
        db.session.commit()
        return jsonify({"message": "Member role updated.", "membership": target.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def remove_member(community_id, user_id):
    community = db.session.get(Community, community_id)
    if not community:
        return jsonify({"error": "Community not found."}), 404

    actor = get_membership(current_user.id, community.id)
    if not can_moderate_community(actor, current_user):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    target = get_membership(user_id, community.id)
    if not target:
        return jsonify({"error": "Member not found."}), 404
    if target.role == "admin" and not can_manage_community(actor, current_user):
        return jsonify({"error": "Cannot remove a community admin."}), 403

    try:
        db.session.delete(target)
        db.session.commit()
        return jsonify({"message": "Member removed."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def get_my_communities():
    rows = CommunityMember.query.filter_by(user_id=current_user.id).order_by(
        CommunityMember.id.desc()
    ).all()
    communities = []
    for row in rows:
        if row.community:
            data = row.community.to_dict(include_member_count=True)
            data["my_role"] = row.role
            communities.append(data)
    return jsonify({"communities": communities}), 200


def get_community_feed(community_id):
    community = db.session.get(Community, community_id)
    if not community:
        return jsonify({"error": "Community not found."}), 404

    post_type = (request.args.get("type") or "").strip().lower()
    query = Post.query.filter_by(community_id=community.id)
    if post_type:
        query = query.filter(Post.type == post_type)
    posts = query.order_by(Post.id.desc()).all()
    return jsonify({"posts": [p.to_dict(include_details=True) for p in posts]}), 200


def get_announcements(community_id):
    community = db.session.get(Community, community_id)
    if not community:
        return jsonify({"error": "Community not found."}), 404
    rows = CommunityAnnouncement.query.filter_by(community_id=community.id).order_by(
        CommunityAnnouncement.is_pinned.desc(),
        CommunityAnnouncement.id.desc(),
    ).all()
    return jsonify({"announcements": [r.to_dict() for r in rows]}), 200


def create_announcement(community_id):
    community = db.session.get(Community, community_id)
    if not community:
        return jsonify({"error": "Community not found."}), 404

    membership = get_membership(current_user.id, community.id)
    if not can_moderate_community(membership, current_user):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    title = str(data.get("title") or "").strip()
    body = str(data.get("body") or "").strip()
    if not title or not body:
        return jsonify({"errors": ["title and body are required."]}), 400

    try:
        row = CommunityAnnouncement(
            community_id=community.id,
            author_id=current_user.id,
            title=title,
            body=body,
            is_pinned=bool(data.get("is_pinned", False)),
        )
        db.session.add(row)
        members = CommunityMember.query.filter_by(community_id=community.id).all()
        for member in members:
            if member.user_id != current_user.id:
                notify(
                    member.user_id,
                    "community_announcement",
                    f"New announcement in {community.name}: {title}",
                    f"/communities/{community.id}/announcements",
                )
        db.session.commit()
        return jsonify({"message": "Announcement created.", "announcement": row.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def update_announcement(community_id, announcement_id):
    row = db.session.get(CommunityAnnouncement, announcement_id)
    if not row or row.community_id != community_id:
        return jsonify({"error": "Announcement not found."}), 404

    membership = get_membership(current_user.id, community_id)
    if not can_moderate_community(membership, current_user):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    try:
        if "title" in data:
            row.title = str(data.get("title") or "").strip()
        if "body" in data:
            row.body = str(data.get("body") or "").strip()
        if "is_pinned" in data:
            row.is_pinned = bool(data.get("is_pinned"))
        db.session.commit()
        return jsonify({"message": "Announcement updated.", "announcement": row.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def delete_announcement(community_id, announcement_id):
    row = db.session.get(CommunityAnnouncement, announcement_id)
    if not row or row.community_id != community_id:
        return jsonify({"error": "Announcement not found."}), 404

    membership = get_membership(current_user.id, community_id)
    if not can_moderate_community(membership, current_user):
        return jsonify({"error": "Access forbidden: insufficient permissions."}), 403

    try:
        db.session.delete(row)
        db.session.commit()
        return jsonify({"message": "Announcement deleted."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def _require_community_post_access(community_id):
    community = db.session.get(Community, community_id)
    if not community:
        return None, (jsonify({"error": "Community not found."}), 404)
    membership = get_membership(current_user.id, community_id)
    if not is_community_member(membership):
        return None, (jsonify({"error": "Join the community before posting."}), 403)
    return community, None
