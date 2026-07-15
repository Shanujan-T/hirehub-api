from flask import jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Report
from app.models.report_model import REPORT_STATUSES, REPORT_TARGET_TYPES
