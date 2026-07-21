from app.extensions import db
from app.models import Company, Job, SavedSearch, User
from app.utils.job_alert_utils import find_matching_saved_searches


def test_find_matching_saved_searches(app):
    with app.app_context():
        employer = User(email="employer2@example.com", full_name="Employer", role="employer")
        employer.set_password("secret123")
        seeker = User(email="alert@example.com", full_name="Alert User", role="seeker")
        seeker.set_password("secret123")
        db.session.add_all([employer, seeker])
        db.session.flush()

        company = Company(owner_id=employer.id, name="Alert Corp")
        db.session.add(company)
        db.session.flush()

        db.session.add(
            SavedSearch(
                user_id=seeker.id,
                keywords="python",
                location="remote",
                min_salary=70000,
            )
        )
        db.session.add(
            SavedSearch(
                user_id=seeker.id,
                keywords="java",
            )
        )
        db.session.commit()

        job = Job(
            company_id=company.id,
            posted_by=employer.id,
            title="Python Developer",
            description="Flask and SQLAlchemy",
            location="Remote",
            salary_min=80000,
            job_type="full_time",
        )

        matches = find_matching_saved_searches(job)
        assert len(matches) == 1
        assert matches[0].keywords == "python"
