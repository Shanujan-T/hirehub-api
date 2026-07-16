import re

from app.extensions import db
from app.models import CommunityMember, Hashtag, Notification, PostMention, User
from app.models.post_media_model import MEDIA_TYPES


def get_membership(user_id, community_id):
    return CommunityMember.query.filter_by(user_id=user_id, community_id=community_id).first()


def is_community_admin(membership):
    return membership and membership.role == "admin"


def is_community_moderator(membership):
    return membership and membership.role in ("admin", "moderator")


def is_community_member(membership):
    return membership is not None


def can_manage_community(membership, user):
    return user.role == "admin" or is_community_admin(membership)


def can_moderate_community(membership, user):
    return user.role == "admin" or is_community_moderator(membership)


def sync_hashtags(post, hashtag_names):
    post.hashtags.clear()
    for raw in hashtag_names or []:
        name = str(raw).strip().lower().lstrip("#")
        if not name:
            continue
        tag = Hashtag.query.filter_by(name=name).first()
        if not tag:
            tag = Hashtag(name=name)
            db.session.add(tag)
        post.hashtags.append(tag)


def extract_hashtags(text):
    if not text:
        return []
    return list({tag.lower() for tag in re.findall(r"#(\w+)", text)})


def sync_mentions_post(post, user_ids):
    PostMention.query.filter_by(post_id=post.id).delete()
    for uid in user_ids or []:
        user = db.session.get(User, int(uid))
        if user:
            db.session.add(PostMention(post_id=post.id, mentioned_user_id=user.id))
            notify(user.id, "mention", f"You were mentioned in a post.", f"/posts/{post.id}")


def sync_mentions_comment(comment, user_ids):
    PostMention.query.filter_by(comment_id=comment.id).delete()
    for uid in user_ids or []:
        user = db.session.get(User, int(uid))
        if user:
            db.session.add(PostMention(comment_id=comment.id, mentioned_user_id=user.id))
            notify(
                user.id,
                "mention",
                "You were mentioned in a comment.",
                f"/posts/{comment.post_id}",
            )


def sync_post_media(post, media_items):
    from app.models import PostMedia

    PostMedia.query.filter_by(post_id=post.id).delete()
    for item in media_items or []:
        media_type = str(item.get("media_type") or "").strip().lower()
        url = str(item.get("url") or "").strip()
        if media_type not in MEDIA_TYPES or not url:
            continue
        db.session.add(
            PostMedia(
                post_id=post.id,
                media_type=media_type,
                url=url,
                title=item.get("title"),
            )
        )


def notify(user_id, type_, message, link_url=None):
    db.session.add(
        Notification(user_id=user_id, type=type_, message=message, link_url=link_url)
    )
