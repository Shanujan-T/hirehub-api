import logging

from flask_cors import CORS
from sqlalchemy.exc import OperationalError, ProgrammingError

from app import create_app
from app.extensions import db

logger = logging.getLogger(__name__)

app = create_app()
CORS(app)


def init_db() -> None:
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables ready.")
        except (OperationalError, ProgrammingError) as exc:
            db.session.rollback()
            detail = exc.orig if getattr(exc, "orig", None) else exc
            logger.warning("Database init failed (API may still start): %s", detail)


init_db()
