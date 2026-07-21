"""Seed example job listings with companies and skills.

Run after admin/demo seeders:
    python -m app.seeders.jobs_seeder
"""

import os
import sys
from datetime import date, timedelta

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

MARKER_COMPANY = "Lanka Digital Labs"


def _get_or_create_skill(db, name, category="Technology"):
    from app.models import Skill

    skill = Skill.query.filter_by(name=name).first()
    if not skill:
        skill = Skill(name=name, category=category)
        db.session.add(skill)
        db.session.flush()
    return skill


def _get_or_create_employer(db, email, full_name, company_name, industry, location):
    from app.models import Company, User

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            email=email,
            full_name=full_name,
            role="employer",
            location=location,
            is_active=True,
        )
        user.set_password("demo1234")
        db.session.add(user)
        db.session.flush()

    company = Company.query.filter_by(name=company_name).first()
    if not company:
        company = Company(
            owner_id=user.id,
            name=company_name,
            industry=industry,
            location=location,
            description=f"{company_name} is hiring through HireHub.",
            website=f"https://{company_name.lower().replace(' ', '')}.example",
            is_verified=True,
        )
        db.session.add(company)
        db.session.flush()

    return user, company


def seed_jobs():
    from app import create_app
    from app.extensions import db
    from app.models import Company, Job, JobSkill, User

    app = create_app()
    with app.app_context():
        if Company.query.filter_by(name=MARKER_COMPANY).first():
            print("Example jobs already seeded. Skipping.")
            return 0

        demo_employer = User.query.filter_by(email="demo.employer@hirehub.test").first()
        demo_company = Company.query.filter_by(name="Demo Tech Co").first() if demo_employer else None

        if demo_employer and not demo_company:
            demo_company = Company(
                owner_id=demo_employer.id,
                name="Demo Tech Co",
                industry="Technology",
                location="Colombo",
                description="Demo technology company for HireHub.",
                is_verified=True,
            )
            db.session.add(demo_company)
            db.session.flush()

        lanka_employer, lanka_company = _get_or_create_employer(
            db,
            "jobs.employer@hirehub.test",
            "Nimal Perera",
            MARKER_COMPANY,
            "Technology",
            "Colombo",
        )
        retail_employer, retail_company = _get_or_create_employer(
            db,
            "retail.employer@hirehub.test",
            "Sarah Fernando",
            "GreenRetail Group",
            "Retail",
            "Kandy",
        )

        skill_names = [
            ("Python", "Technology"),
            ("JavaScript", "Technology"),
            ("React", "Technology"),
            ("MySQL", "Technology"),
            ("SQL", "Technology"),
            ("Flask", "Technology"),
            ("Communication", "Soft Skills"),
            ("Excel", "Business"),
            ("Marketing", "Business"),
            ("Customer Service", "Soft Skills"),
        ]
        skills = {name: _get_or_create_skill(db, name, cat) for name, cat in skill_names}

        deadline = date.today() + timedelta(days=45)

        jobs_spec = [
            {
                "company": demo_company,
                "poster": demo_employer,
                "title": "Python Developer",
                "description": "Build and maintain REST APIs with Python and MySQL. Collaborate with a small agile team on local fintech products.",
                "category": "Technology",
                "job_type": "full_time",
                "experience_level": "mid",
                "location": "Colombo",
                "salary_min": 120000,
                "salary_max": 180000,
                "skill_names": ["Python", "MySQL", "Flask"],
            },
            {
                "company": lanka_company,
                "poster": lanka_employer,
                "title": "Frontend Developer (React)",
                "description": "Implement responsive UIs for our hiring platform clients. Experience with React, TypeScript, and REST integration preferred.",
                "category": "Technology",
                "job_type": "full_time",
                "experience_level": "junior",
                "location": "Colombo",
                "salary_min": 90000,
                "salary_max": 140000,
                "skill_names": ["JavaScript", "React"],
            },
            {
                "company": lanka_company,
                "poster": lanka_employer,
                "title": "Junior Software Engineer",
                "description": "Graduate-friendly role with mentorship. Work on internal tools using Python and SQL with code reviews and pair programming.",
                "category": "Technology",
                "job_type": "full_time",
                "experience_level": "entry",
                "location": "Colombo / Hybrid",
                "salary_min": 70000,
                "salary_max": 95000,
                "skill_names": ["Python", "SQL", "Communication"],
            },
            {
                "company": lanka_company,
                "poster": lanka_employer,
                "title": "Software Engineering Intern",
                "description": "3-month paid internship. Assist with bug fixes, documentation, and feature testing on web applications.",
                "category": "Technology",
                "job_type": "internship",
                "experience_level": "entry",
                "location": "Colombo",
                "salary_min": 30000,
                "salary_max": 45000,
                "skill_names": ["JavaScript", "Communication"],
            },
            {
                "company": lanka_company,
                "poster": lanka_employer,
                "title": "DevOps Engineer (Contract)",
                "description": "6-month contract to improve CI/CD pipelines and cloud deployment workflows for client projects.",
                "category": "Technology",
                "job_type": "contract",
                "experience_level": "senior",
                "location": "Remote",
                "salary_min": 200000,
                "salary_max": 280000,
                "skill_names": ["Python", "Communication"],
            },
            {
                "company": retail_company,
                "poster": retail_employer,
                "title": "Marketing Coordinator",
                "description": "Support digital campaigns, social media, and in-store promotions for our retail brands across central province.",
                "category": "Marketing",
                "job_type": "full_time",
                "experience_level": "junior",
                "location": "Kandy",
                "salary_min": 55000,
                "salary_max": 75000,
                "skill_names": ["Marketing", "Communication", "Excel"],
            },
            {
                "company": retail_company,
                "poster": retail_employer,
                "title": "Customer Support Associate",
                "description": "Handle customer inquiries via phone and email. Weekend shifts required. Training provided.",
                "category": "Customer Service",
                "job_type": "part_time",
                "experience_level": "entry",
                "location": "Kandy",
                "salary_min": 35000,
                "salary_max": 50000,
                "skill_names": ["Customer Service", "Communication"],
            },
            {
                "company": retail_company,
                "poster": retail_employer,
                "title": "Store Operations Manager",
                "description": "Lead daily store operations, staff scheduling, and inventory reporting for a busy retail location.",
                "category": "Operations",
                "job_type": "full_time",
                "experience_level": "mid",
                "location": "Kandy",
                "salary_min": 85000,
                "salary_max": 110000,
                "skill_names": ["Excel", "Communication"],
            },
            {
                "company": lanka_company,
                "poster": lanka_employer,
                "title": "Data Analyst",
                "description": "Analyze product usage data, build SQL reports, and present insights to stakeholders monthly.",
                "category": "Data",
                "job_type": "full_time",
                "experience_level": "mid",
                "location": "Colombo / Hybrid",
                "salary_min": 100000,
                "salary_max": 150000,
                "skill_names": ["SQL", "Excel", "Communication"],
            },
            {
                "company": demo_company or lanka_company,
                "poster": demo_employer or lanka_employer,
                "title": "Full Stack Developer",
                "description": "Own features end-to-end: React frontend, Python backend, and MySQL databases. Remote-friendly team.",
                "category": "Technology",
                "job_type": "full_time",
                "experience_level": "senior",
                "location": "Remote",
                "salary_min": 180000,
                "salary_max": 250000,
                "skill_names": ["Python", "React", "MySQL", "JavaScript"],
            },
        ]

        created = 0
        for spec in jobs_spec:
            company = spec["company"]
            poster = spec["poster"]
            if not company or not poster:
                continue

            existing = Job.query.filter_by(
                title=spec["title"],
                company_id=company.id,
            ).first()
            if existing:
                continue

            job = Job(
                company_id=company.id,
                posted_by=poster.id,
                title=spec["title"],
                description=spec["description"],
                category=spec["category"],
                job_type=spec["job_type"],
                experience_level=spec["experience_level"],
                location=spec["location"],
                salary_min=spec["salary_min"],
                salary_max=spec["salary_max"],
                deadline=deadline,
                status="open",
            )
            db.session.add(job)
            db.session.flush()

            for skill_name in spec["skill_names"]:
                db.session.add(JobSkill(job_id=job.id, skill_id=skills[skill_name].id))

            created += 1

        db.session.commit()
        print(f"Seeded {created} example jobs across HireHub employer companies.")
        print("  Sample employer logins (password: demo1234):")
        print("  - jobs.employer@hirehub.test (Lanka Digital Labs)")
        print("  - retail.employer@hirehub.test (GreenRetail Group)")
        return 0


if __name__ == "__main__":
    raise SystemExit(seed_jobs())
