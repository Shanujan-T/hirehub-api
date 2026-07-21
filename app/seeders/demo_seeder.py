"""Minimal demo seed for viva: status history + skill-matched recommendations.

Run after admin seeder when DEMO_SEED=true:
    python -m app.seeders.demo_seeder
"""

import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()


def seed_demo():
    from app import create_app
    from app.extensions import db
    from app.models import (
        Application,
        ApplicationStatusLog,
        Company,
        Job,
        JobSkill,
        Skill,
        User,
        UserSkill,
    )

    app = create_app()
    with app.app_context():
        if User.query.filter_by(email="demo.seeker@hirehub.test").first():
            print("Demo data already seeded. Skipping.")
            return 0

        python_skill = Skill.query.filter_by(name="Python").first()
        if not python_skill:
            python_skill = Skill(name="Python", category="Technology")
            db.session.add(python_skill)
            db.session.flush()

        mysql_skill = Skill.query.filter_by(name="MySQL").first()
        if not mysql_skill:
            mysql_skill = Skill(name="MySQL", category="Technology")
            db.session.add(mysql_skill)
            db.session.flush()

        seeker = User(
            email="demo.seeker@hirehub.test",
            full_name="Demo Seeker",
            role="seeker",
            location="Colombo",
            is_active=True,
        )
        seeker.set_password("demo1234")
        employer = User(
            email="demo.employer@hirehub.test",
            full_name="Demo Employer",
            role="employer",
            is_active=True,
        )
        employer.set_password("demo1234")
        db.session.add_all([seeker, employer])
        db.session.flush()

        db.session.add_all([
            UserSkill(user_id=seeker.id, skill_id=python_skill.id, level="intermediate"),
            UserSkill(user_id=seeker.id, skill_id=mysql_skill.id, level="beginner"),
        ])

        company = Company(
            owner_id=employer.id,
            name="Demo Tech Co",
            industry="Technology",
            location="Colombo",
            is_verified=True,
        )
        db.session.add(company)
        db.session.flush()

        job = Job(
            company_id=company.id,
            posted_by=employer.id,
            title="Python Developer",
            description="Build APIs with Python and MySQL.",
            category="Technology",
            job_type="full_time",
            experience_level="mid",
            location="Colombo",
            status="open",
        )
        db.session.add(job)
        db.session.flush()
        db.session.add_all([
            JobSkill(job_id=job.id, skill_id=python_skill.id),
            JobSkill(job_id=job.id, skill_id=mysql_skill.id),
        ])

        application = Application(
            job_id=job.id,
            seeker_id=seeker.id,
            cover_letter="Excited to apply for this Python role.",
            status="pending",
        )
        db.session.add(application)
        db.session.flush()

        db.session.add(
            ApplicationStatusLog(
                application_id=application.id,
                old_status=None,
                new_status="pending",
                changed_by=seeker.id,
            )
        )
        db.session.commit()
        print("Demo seeker/employer/job/application seeded for viva demo.")
        print("  seeker: demo.seeker@hirehub.test / demo1234")
        print("  employer: demo.employer@hirehub.test / demo1234")
        return 0


if __name__ == "__main__":
    raise SystemExit(seed_demo())
