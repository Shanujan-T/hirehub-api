"""Seed community feed posts with cover images.

Run after community content seeder:
    python -m app.seeders.image_posts_seeder
"""

import os
import struct
import sys
import zlib

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

MARKER_TITLE = "My home office setup for remote work"


def _write_simple_png(path: str, width: int, height: int, rgb: tuple[int, int, int]) -> None:
    row = b"\x00" + bytes(rgb) * width
    raw = row * height
    compressed = zlib.compress(raw, 9)

    def png_chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", ihdr)
    png += png_chunk(b"IDAT", compressed)
    png += png_chunk(b"IEND", b"")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(png)


def _authors(db):
    from app.models import User

    seeker = User.query.filter_by(email="demo.seeker@hirehub.test").first()
    employer = User.query.filter_by(email="demo.employer@hirehub.test").first()
    admin = User.query.filter_by(role="admin").first()
    authors = [u for u in (seeker, employer, admin) if u]
    if not authors:
        raise RuntimeError("No users found. Run admin/demo seeders first.")
    return seeker or authors[0], employer or authors[0], admin or authors[0]


def seed_image_posts():
    from app import create_app
    from app.extensions import db
    from app.models import Post

    app = create_app()
    with app.app_context():
        if Post.query.filter_by(title=MARKER_TITLE).first():
            print("Image posts already seeded. Skipping.")
            return 0

        seeker, employer, admin = _authors(db)
        upload_dir = app.config["POST_IMAGE_UPLOAD_FOLDER"]

        posts_spec = [
            {
                "author_id": seeker.id,
                "title": MARKER_TITLE,
                "body": (
                    "Sharing my desk layout after six months of remote work — dual monitor, "
                    "good lighting, and a plant that somehow survives standups. "
                    "What does your workspace look like?"
                ),
                "type": "discussion",
                "filename": "office_setup.png",
                "color": (12, 68, 183),
            },
            {
                "author_id": seeker.id,
                "title": "Celebrating my first full-time offer!",
                "body": (
                    "Signed the contract today after a long internship search. "
                    "Grateful for everyone who reviewed my portfolio and gave interview tips here."
                ),
                "type": "success_story",
                "filename": "offer_celebration.png",
                "color": (245, 158, 11),
            },
            {
                "author_id": employer.id,
                "title": "We're growing the API team — open roles",
                "body": (
                    "Lanka Digital Labs is hiring backend engineers (Python/Flask). "
                    "Hybrid in Colombo, mentorship for mid-level devs, and clear growth paths."
                ),
                "type": "job_share",
                "filename": "hiring_banner.png",
                "color": (16, 185, 129),
            },
            {
                "author_id": admin.id,
                "title": "Visual guide: structuring your tech portfolio",
                "body": (
                    "A strong portfolio page shows three things: problem, approach, and outcome. "
                    "Attach screenshots or architecture diagrams when you can — they help recruiters scan faster."
                ),
                "type": "guidance",
                "filename": "portfolio_guide.png",
                "color": (90, 41, 154),
            },
            {
                "author_id": seeker.id,
                "title": "Favorite co-working corner in Colombo",
                "body": (
                    "Found a quiet spot with stable Wi‑Fi near Bambalapitiya. "
                    "Great for focus days when home is too noisy. Happy to share details in the comments."
                ),
                "type": "discussion",
                "filename": "coworking_space.png",
                "color": (34, 211, 238),
            },
        ]

        for spec in posts_spec:
            post = Post(
                author_id=spec["author_id"],
                title=spec["title"],
                body=spec["body"],
                type=spec["type"],
            )
            db.session.add(post)
            db.session.flush()

            stored_name = f"{post.id}_{spec['filename']}"
            file_path = os.path.join(upload_dir, stored_name)
            _write_simple_png(file_path, 960, 540, spec["color"])
            post.image_url = f"/uploads/posts/{stored_name}"

        db.session.commit()
        print(f"Seeded {len(posts_spec)} image posts.")
        return 0


if __name__ == "__main__":
    raise SystemExit(seed_image_posts())
