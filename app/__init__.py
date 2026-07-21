from flask import Flask, jsonify, send_from_directory
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.config import Config
from app.extensions import db, jwt, limiter
from app.routes import register_blueprints


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    limiter.enabled = app.config.get("RATELIMIT_ENABLED", True)

    # Import all models so metadata is registered before create_all
    from app.models import User  # triggers app.models.__init__ (all models)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return db.session.get(User, int(identity))

    register_blueprints(app)

    @app.route("/uploads/resumes/<path:filename>", methods=["GET"])
    def serve_resume(filename):
        return send_from_directory(app.config["RESUME_UPLOAD_FOLDER"], filename)

    @app.route("/uploads/posts/<path:filename>", methods=["GET"])
    def serve_post_image(filename):
        return send_from_directory(app.config["POST_IMAGE_UPLOAD_FOLDER"], filename)

    @app.route("/uploads/jobs/<path:filename>", methods=["GET"])
    def serve_job_image(filename):
        return send_from_directory(app.config["JOB_IMAGE_UPLOAD_FOLDER"], filename)

    @app.route("/uploads/companies/<path:filename>", methods=["GET"])
    def serve_company_logo(filename):
        return send_from_directory(app.config["COMPANY_LOGO_UPLOAD_FOLDER"], filename)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/", methods=["GET"])
    def api_home():
        return jsonify({
            "message": "Local Job Finder API",
            "version": "1.0",
            "endpoints": {
                "auth": "/api/auth",
                "users": "/api/users",
                "candidates": "/api/candidates",
                "companies": "/api/companies",
                "skills": "/api/skills",
                "jobs": "/api/jobs",
                "applications": "/api/applications",
                "posts": "/api/posts",
                "communities": "/api/communities",
                "referrals": "/api/referrals",
                "mentorships": "/api/mentorships",
                "mentors": "/api/mentors",
                "reports": "/api/reports",
                "dashboard": "/api/me/dashboard",
            },
        })

    @app.errorhandler(OperationalError)
    def handle_operational_error(err):
        db.session.rollback()
        orig = getattr(err, "orig", None)
        code = orig.args[0] if orig and orig.args else None
        if code == 1049:
            return jsonify({"error": "Invalid database name configured."}), 500
        if code in (2003, 2002):
            return jsonify({"error": "MySQL server is not running or not reachable."}), 503
        return jsonify({"error": "Database connection failed."}), 500

    @app.errorhandler(ProgrammingError)
    def handle_programming_error(err):
        db.session.rollback()
        return jsonify({"error": "Invalid database name configured."}), 500

    @app.errorhandler(500)
    def handle_internal_error(err):
        return jsonify({"error": "An internal server error occurred."}), 500

    return app
