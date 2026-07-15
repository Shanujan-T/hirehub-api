from flask import jsonify, request
from flask_jwt_extended import current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Mentorship, User
