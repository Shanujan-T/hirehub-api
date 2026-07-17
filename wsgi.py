import logging

from flask_cors import CORS

from app import create_app

logger = logging.getLogger(__name__)

app = create_app()
CORS(app)
