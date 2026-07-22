from app.seeders.admin_seeder import seed_admin
from app.seeders.community_content_seeder import seed_community_content
from app.seeders.demo_seeder import seed_demo
from app.seeders.image_posts_seeder import seed_image_posts
from app.seeders.quiz_seeder import seed_skill_quizzes


def run_all():
    print("Running admin seeder...")
    seed_admin()
    print("Running demo seeder...")
    seed_demo()
    print("Running jobs seeder...")
    seed_jobs()
    print("Running community content seeder...")
    seed_community_content()
    print("Running image posts seeder...")
    seed_image_posts()
    print("Running skill quiz seeder...")
    seed_skill_quizzes()


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        from app.extensions import db

        db.create_all()
        run_all()
