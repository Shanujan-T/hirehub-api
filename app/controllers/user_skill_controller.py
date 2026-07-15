from datetime import datetime

from flask import jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Skill, UserSkill
from app.models.user_skill_model import SKILL_LEVELS
from app.utils.csv_utils import parse_csv_file, rows_to_csv_response


def get_my_skills():
    rows = UserSkill.query.filter_by(user_id=current_user.id).order_by(UserSkill.id.desc()).all()
    return jsonify({"user_skills": [r.to_dict() for r in rows]}), 200
