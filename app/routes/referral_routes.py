from flask import Blueprint

from app.controllers import referral_controller as ctrl
from app.middleware import jwt_required_active

referrals_bp = Blueprint("referrals", __name__, url_prefix="/api/referrals")
my_referrals_bp = Blueprint("my_referrals", __name__, url_prefix="/api/my")


@referrals_bp.route("", methods=["GET"])
@jwt_required_active
def list_referrals():
    return ctrl.get_referrals()


@referrals_bp.route("", methods=["POST"])
@jwt_required_active
def create_referral():
    return ctrl.create_referral()


@my_referrals_bp.route("/referrals", methods=["GET"])
@jwt_required_active
def my_referrals():
    return ctrl.get_my_referrals()


@referrals_bp.route("/<int:referral_id>", methods=["GET"])
@jwt_required_active
def get_referral(referral_id):
    return ctrl.get_referral(referral_id)


@referrals_bp.route("/<int:referral_id>/status", methods=["PATCH"])
@jwt_required_active
def update_referral_status(referral_id):
    return ctrl.update_referral_status(referral_id)
