import os
import subprocess
import sys

from flask_cors import CORS
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError, ProgrammingError

from app import create_app

# Gunicorn settings when started with: gunicorn -c run run:app
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
workers = 1
threads = 4
timeout = 120
accesslog = "-"
errorlog = "-"

app = create_app()

CORS(
    app,
    resources={
        r"/api/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]},
        r"/uploads/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]},
    },
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)

_SCHEMA_ALTERS = [
    "ALTER TABLE posts ADD COLUMN community_id INT NULL",
    "ALTER TABLE posts ADD COLUMN link_url VARCHAR(500) NULL",
    "ALTER TABLE posts ADD COLUMN image_url VARCHAR(500) NULL",
    "ALTER TABLE comments ADD COLUMN parent_id INT NULL",
    "ALTER TABLE mentorships ADD COLUMN community_id INT NULL",
    "ALTER TABLE mentorships ADD COLUMN focus_area VARCHAR(30) NULL",
    "ALTER TABLE companies ADD COLUMN is_verified TINYINT(1) NOT NULL DEFAULT 0",
    "ALTER TABLE user_skills ADD COLUMN verified TINYINT(1) NOT NULL DEFAULT 0",
    "ALTER TABLE user_skills ADD COLUMN verified_by INT NULL",
    "ALTER TABLE jobs ADD COLUMN image_url VARCHAR(500) NULL",
]


def _apply_schema_updates(db) -> None:
    inspector = inspect(db.engine)
    for statement in _SCHEMA_ALTERS:
        table = statement.split(" ")[2]
        column = statement.split(" ")[5]
        if not inspector.has_table(table):
            continue
        columns = {col["name"] for col in inspector.get_columns(table)}
        if column not in columns:
            db.session.execute(text(statement))
    db.session.commit()


def init_db() -> None:
    with app.app_context():
        from app.extensions import db

        try:
            db.create_all()
            _apply_schema_updates(db)
        except (OperationalError, ProgrammingError) as exc:
            db.session.rollback()
            print("\n[ERROR] Could not connect to MySQL or create tables.")
            print("Check DB_HOST, DB_USER, DB_PASSWORD, and DB_NAME in your .env file.")
            print(f"Details: {exc.orig if getattr(exc, 'orig', None) else exc}\n")
            raise SystemExit(1) from exc
        except Exception as exc:
            db.session.rollback()
            print(f"\n[WARN] Schema update skipped: {exc}\n")


init_db()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))

    if sys.platform == "win32":
        from waitress import serve

        print(f"Starting server on http://127.0.0.1:{port}")
        serve(app, host="0.0.0.0", port=port, threads=4)
    else:
        subprocess.run(
            [sys.executable, "-m", "gunicorn", "-c", "run", "run:app"],
            check=True,
        )
