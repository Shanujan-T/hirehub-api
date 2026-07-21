"""Seed example communities and community feed posts.

Run after admin (and optionally demo) seeders:
    python -m app.seeders.community_content_seeder
"""

import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

MARKER_SLUG = "colombo-tech-professionals"


def _authors(db):
    from app.models import User

    admin = User.query.filter_by(role="admin").first()
    seeker = User.query.filter_by(email="demo.seeker@hirehub.test").first()
    employer = User.query.filter_by(email="demo.employer@hirehub.test").first()

    authors = [u for u in (admin, seeker, employer) if u]
    if not authors:
        seeker = User(
            email="community.author@hirehub.test",
            full_name="Community Author",
            role="seeker",
            location="Colombo",
            is_active=True,
        )
        seeker.set_password("demo1234")
        db.session.add(seeker)
        db.session.flush()
        authors = [seeker]

    return authors


def seed_community_content():
    from app import create_app
    from app.extensions import db
    from app.models import Community, CommunityMember, Post

    app = create_app()
    with app.app_context():
        if Community.query.filter_by(slug=MARKER_SLUG).first():
            print("Example communities and posts already seeded. Skipping.")
            return 0

        authors = _authors(db)
        admin_user = authors[0]
        seeker = next((u for u in authors if u.role == "seeker"), authors[0])
        employer = next((u for u in authors if u.role == "employer"), authors[0])

        communities_data = [
            {
                "name": "Colombo Tech Professionals",
                "slug": MARKER_SLUG,
                "type": "profession",
                "description": "A space for software engineers, designers, and IT professionals in Colombo to share opportunities and advice.",
                "location": "Colombo",
                "industry": "Technology",
                "created_by": admin_user.id,
            },
            {
                "name": "University Careers Network",
                "slug": "university-careers-network",
                "type": "university",
                "description": "Students and alumni connecting over internships, graduate roles, and career guidance.",
                "location": "Sri Lanka",
                "created_by": seeker.id,
            },
            {
                "name": "Remote Workers Sri Lanka",
                "slug": "remote-workers-sri-lanka",
                "type": "location",
                "description": "Tips, job leads, and community support for remote and hybrid professionals based in Sri Lanka.",
                "location": "Sri Lanka",
                "created_by": seeker.id,
            },
            {
                "name": "HR & Hiring Hub",
                "slug": "hr-hiring-hub",
                "type": "industry",
                "description": "Employers and recruiters sharing hiring updates, interview best practices, and talent market insights.",
                "industry": "Human Resources",
                "created_by": employer.id,
            },
            {
                "name": "Python Developers SL",
                "slug": "python-developers-sl",
                "type": "interest",
                "description": "Discuss Python frameworks, backend roles, learning resources, and local Python meetups.",
                "industry": "Technology",
                "created_by": admin_user.id,
            },
        ]

        communities = []
        for data in communities_data:
            community = Community(**data, is_public=True)
            db.session.add(community)
            communities.append(community)
        db.session.flush()

        for community in communities:
            db.session.add(
                CommunityMember(
                    community_id=community.id,
                    user_id=community.created_by,
                    role="admin",
                )
            )
            if seeker.id != community.created_by:
                db.session.add(
                    CommunityMember(
                        community_id=community.id,
                        user_id=seeker.id,
                        role="member",
                    )
                )
            if employer.id not in (community.created_by, seeker.id):
                db.session.add(
                    CommunityMember(
                        community_id=community.id,
                        user_id=employer.id,
                        role="member",
                    )
                )

        tech_comm, uni_comm, remote_comm, hr_comm, python_comm = communities

        posts_data = [
            # General community feed (no community_id)
            {
                "author_id": seeker.id,
                "title": "How do you prepare for your first technical interview?",
                "body": "I have a backend interview next week focusing on Python and SQL. What topics should I revise, and how did you structure your prep?",
                "type": "discussion",
            },
            {
                "author_id": employer.id,
                "title": "We're hiring: Junior Full Stack Developer",
                "body": "Our team is growing! Looking for a junior developer comfortable with React and REST APIs. Remote-friendly with occasional office days in Colombo.",
                "type": "job_opportunity",
            },
            {
                "author_id": admin_user.id,
                "title": "Free resume review workshop this Friday",
                "body": "Join our live session on tailoring your CV for local tech roles. Bring one resume and we'll walk through improvements together.",
                "type": "event",
                "link_url": "https://hirehub.example/events/resume-workshop",
            },
            {
                "author_id": seeker.id,
                "title": "My journey from intern to full-time offer",
                "body": "Six months ago I started as an intern. Today I signed a full-time contract. Happy to answer questions about making the most of internship programs.",
                "type": "success_story",
            },
            # Community-scoped posts
            {
                "author_id": seeker.id,
                "community_id": tech_comm.id,
                "title": "Best co-working spots in Colombo for developers?",
                "body": "Looking for reliable Wi‑Fi and a quiet environment. What places do you recommend for deep work days?",
                "type": "discussion",
            },
            {
                "author_id": employer.id,
                "community_id": tech_comm.id,
                "title": "Hiring announcement: Python Developer (Mid-level)",
                "body": "We're expanding our API team. Stack: Python, Flask, MySQL. DM me or apply via HireHub if you're interested.",
                "type": "hiring_announcement",
            },
            {
                "author_id": admin_user.id,
                "community_id": uni_comm.id,
                "title": "Internship applications — what recruiters actually read first",
                "body": "After reviewing hundreds of graduate CVs, here's what stands out: clear project summaries, GitHub links that work, and a short cover letter tied to the role.",
                "type": "career_advice",
            },
            {
                "author_id": seeker.id,
                "community_id": uni_comm.id,
                "title": "Summer internship at a fintech — my interview experience",
                "body": "The process had an online test, a technical screen, and a culture fit chat. Sharing the types of questions I got in case it helps others applying.",
                "type": "interview_experience",
            },
            {
                "author_id": seeker.id,
                "community_id": remote_comm.id,
                "title": "Tools for staying productive when working from home",
                "body": "I use time blocking, a dedicated desk setup, and async standups. What routines help you stay focused across time zones?",
                "type": "discussion",
            },
            {
                "author_id": employer.id,
                "community_id": hr_comm.id,
                "title": "Structured interviews reduce bad hires",
                "body": "We moved to scorecards and consistent question sets for every candidate. Quality of hire improved and feedback loops got much clearer.",
                "type": "career_advice",
            },
            {
                "author_id": admin_user.id,
                "community_id": python_comm.id,
                "title": "Recommended Python learning path for 2026",
                "body": "Start with core Python, then Flask or FastAPI, SQL basics, and one small deployed project. Official docs + one portfolio app beat endless tutorials.",
                "type": "learning_resource",
                "link_url": "https://docs.python.org/3/tutorial/",
            },
            {
                "author_id": seeker.id,
                "community_id": python_comm.id,
                "title": "Referral request: backend role with Django experience",
                "body": "A friend is looking for a Django backend position (2+ years). Strong on REST APIs and PostgreSQL. Happy to share their profile privately.",
                "type": "referral_request",
            },
        ]

        for post_data in posts_data:
            db.session.add(Post(**post_data))

        db.session.commit()
        print(f"Seeded {len(communities)} communities and {len(posts_data)} posts.")
        return 0


if __name__ == "__main__":
    raise SystemExit(seed_community_content())
