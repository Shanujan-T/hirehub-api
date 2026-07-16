from flask_cors import CORS
from sqlalchemy.exc import OperationalError, ProgrammingError

from app import create_app

import os

from wsgi import app, init_db

app = create_app()
CORS(app)

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
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug, host="0.0.0.0", port=port)