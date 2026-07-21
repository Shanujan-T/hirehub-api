from flask import Blueprint

from app.controllers import analytics_controller as ctrl
from app.middleware import require_role

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/analytics", methods=["GET"])
@require_role("admin")
def get_analytics():
    return ctrl.get_admin_analytics()
