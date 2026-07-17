from flask_cors import CORS
from sqlalchemy.exc import OperationalError, ProgrammingError

from wsgi import app

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
    init_db()
