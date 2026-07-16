from app.routes.auth_routes import auth_bp
from app.routes.user_routes import users_bp
from app.routes.candidate_routes import candidates_bp
from app.routes.company_routes import companies_bp, my_company_bp
from app.routes.skill_routes import skills_bp
from app.routes.user_skill_routes import my_skills_bp
from app.routes.interest_routes import interests_bp
from app.routes.user_interest_routes import my_interests_bp
from app.routes.job_routes import jobs_bp, my_saved_jobs_bp
from app.routes.application_routes import applications_bp
from app.routes.post_routes import posts_bp, comments_bp, my_bookmarks_bp
from app.routes.report_routes import reports_bp
from app.routes.dashboard_routes import dashboard_bp
from app.routes.mentorship_routes import mentorships_bp, my_mentorships_bp, mentors_bp
from app.routes.conversation_routes import conversations_bp, my_conversations_bp, messages_bp
from app.routes.notification_routes import notifications_bp, my_notifications_bp
from app.routes.community_routes import communities_bp, my_communities_bp
from app.routes.referral_routes import referrals_bp, my_referrals_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(candidates_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(my_company_bp)
    app.register_blueprint(skills_bp)
    app.register_blueprint(my_skills_bp)
    app.register_blueprint(interests_bp)
    app.register_blueprint(my_interests_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(my_saved_jobs_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(my_bookmarks_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(mentorships_bp)
    app.register_blueprint(my_mentorships_bp)
    app.register_blueprint(mentors_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(my_conversations_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(my_notifications_bp)
    app.register_blueprint(communities_bp)
    app.register_blueprint(my_communities_bp)
    app.register_blueprint(referrals_bp)
    app.register_blueprint(my_referrals_bp)
