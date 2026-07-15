from app.seeders.admin_seeder import seed_admin


def run_all():
    print("Running admin seeder...")
    seed_admin()


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        from app.extensions import db

        db.create_all()
        run_all()
