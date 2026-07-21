from app.extensions import db
from app.models import Company


def test_create_and_list_jobs(client, employer_user, auth_headers):
    headers = auth_headers("employer@example.com", "secret123")

    company = Company(
        owner_id=employer_user.id,
        name="Acme Corp",
        industry="Technology",
        location="Remote",
    )
    db.session.add(company)
    db.session.commit()

    create = client.post(
        "/api/jobs",
        json={
            "title": "Backend Developer",
            "description": "Build APIs with Flask",
            "category": "Engineering",
            "job_type": "full_time",
            "experience_level": "mid",
            "location": "Remote",
            "salary_min": 80000,
            "salary_max": 120000,
        },
        headers=headers,
    )

    assert create.status_code == 201
    job = create.get_json()["job"]
    assert job["title"] == "Backend Developer"
    assert job["company_id"] == company.id

    listing = client.get("/api/jobs?q=backend")
    assert listing.status_code == 200
    jobs = listing.get_json()["jobs"]
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Backend Developer"
