from flask_cors import CORS
from sqlalchemy.exc import OperationalError, ProgrammingError

from app import create_app

app = create_app()
CORS(app)


def init_db() -> None:
    with app.app_context():
        from app.extensions import db

        try:
            db.create_all()
        except (OperationalError, ProgrammingError) as exc:
            db.session.rollback()
            print("\n[ERROR] Could not connect to MySQL or create tables.")
            print("Check DB_HOST, DB_USER, DB_PASSWORD, and DB_NAME in your .env file.")
            print(f"Details: {exc.orig if getattr(exc, 'orig', None) else exc}\n")
            raise SystemExit(1) from exc


if __name__ == "__main__":
    import os
    import subprocess
    import sys

    subprocess.run([sys.executable, "migrate_schema.py"], check=False)
    init_db()

    port = int(os.getenv("PORT", "5000"))

    if sys.platform == "win32":
        from waitress import serve

        print(f"Starting server on http://127.0.0.1:{port}")
        serve(app, host="0.0.0.0", port=port, threads=4)
    else:
        subprocess.run(
            [sys.executable, "-m", "gunicorn", "-c", "gunicorn.conf.py", "run:app"],
            check=True,
        )
