"""Apply schema updates for communities, rich posts, referrals, and mentorship."""

from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError, ProgrammingError

from app import create_app
from app.extensions import db


ALTERS = [
    "ALTER TABLE posts ADD COLUMN community_id INT NULL",
    "ALTER TABLE posts ADD COLUMN link_url VARCHAR(500) NULL",
    "ALTER TABLE comments ADD COLUMN parent_id INT NULL",
    "ALTER TABLE mentorships ADD COLUMN community_id INT NULL",
    "ALTER TABLE mentorships ADD COLUMN focus_area VARCHAR(30) NULL",
]


def column_exists(table, column):
    inspector = inspect(db.engine)
    return column in {col["name"] for col in inspector.get_columns(table)}


def table_exists(table):
    return inspect(db.engine).has_table(table)


def run():
    app = create_app()
    with app.app_context():
        try:
            db.create_all()

            for statement in ALTERS:
                table = statement.split(" ")[2]
                column = statement.split(" ")[5]
                if table_exists(table) and not column_exists(table, column):
                    db.session.execute(text(statement))
                    print(f"Applied: {statement}")

            db.session.commit()
            print("Schema migration complete.")
        except (OperationalError, ProgrammingError) as exc:
            db.session.rollback()
            print(f"Schema migration skipped (database unavailable): {exc}")
        except Exception as exc:
            db.session.rollback()
            print(f"Schema migration skipped: {exc}")


if __name__ == "__main__":
    run()
