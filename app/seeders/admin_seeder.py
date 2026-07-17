"""Create the platform admin from environment variables.

Usage:
    npm run seed:admin
    # or
    python run_seeders.py
    # or
    python -m app.seeders.admin_seeder

Requires ADMIN_EMAIL and ADMIN_PASSWORD in the environment / .env.
Never hard-code admin credentials in source.
"""

import os
import sys

from dotenv import load_dotenv

# Allow running as `python -m seeders.admin_seeder` from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def seed_admin():
    from app import create_app
    from app.extensions import db
    from app.models import User

    email = (os.getenv("ADMIN_EMAIL") or "").strip()
    password = os.getenv("ADMIN_PASSWORD") or ""
    full_name = (os.getenv("ADMIN_FULL_NAME") or "Platform Admin").strip()

    if not email or not password:
        print("ERROR: ADMIN_EMAIL and ADMIN_PASSWORD must be set in the environment.")
        return 1

    if len(password) < 6:
        print("ERROR: ADMIN_PASSWORD must be at least 6 characters.")
        return 1

    app = create_app()
    with app.app_context():
        existing = User.query.filter_by(email=email).first()
        if existing:
            if existing.role == "admin":
                print(f"Admin already exists for {email} (id={existing.id}). Skipping.")
                return 0
            print(
                f"ERROR: A non-admin user already exists with email {email}. "
                "Refuse to overwrite. Use a different ADMIN_EMAIL."
            )
            return 1

        admin = User(
            email=email,
            full_name=full_name,
            role="admin",
            is_active=True,
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin created successfully: {email} (id={admin.id})")
        return 0


if __name__ == "__main__":
    raise SystemExit(seed_admin())
