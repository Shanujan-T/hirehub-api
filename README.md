# HireHub / Local Job Finder — API

Flask REST API for the Local Job Finder project.

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env              # then edit DB_* and ADMIN_* values
```

Create the MySQL database named in `DB_NAME`, then:

```bash
python run.py
```

Tables are created on startup via `db.create_all()`.

## Admin account (no public registration)

Admins cannot be created through `POST /api/auth/register`. Run the seeder:

```bash
npm run seed:admin
# or
python run_seeders.py
# or
python -m app.seeders.admin_seeder
```

Uses `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and optional `ADMIN_FULL_NAME` from `.env`. Skips if that admin email already exists. Password is hashed before save.

## Auth roles

| Role | How created |
|------|-------------|
| `seeker` | Public register (default; aliases `jobseeker` accepted) |
| `employer` | Public register with `role` / `account_type` = `employer` |
| `admin` | Seeder only |

Any `role=admin` in register/profile/user update/import is rejected or ignored. Admin routes use `@require_role("admin")`.

## Sample JSON data (all entities)

One connected demo dataset matching API `to_dict()` shapes:

```json
{
  "users": [
    {
      "id": 1,
      "email": "admin@localjobs.test",
      "role": "admin",
      "full_name": "Platform Admin",
      "bio": null,
      "location": "Vavuniya",
      "phone": null,
      "education_level": null,
      "resume_url": null,
      "avatar_url": null,
      "is_active": true,
      "created_at": "2026-07-14T10:00:00+00:00"
    },
    {
      "id": 2,
      "email": "kavitha@localjobs.test",
      "role": "employer",
      "full_name": "Kavitha Raj",
      "bio": "Hiring manager at Vavuniya Tech Solutions.",
      "location": "Vavuniya",
      "phone": "+94771234567",
      "education_level": null,
      "resume_url": null,
      "avatar_url": null,
      "is_active": true,
      "created_at": "2026-07-14T10:05:00+00:00"
    },
    {
      "id": 3,
      "email": "shanujan@localjobs.test",
      "role": "seeker",
      "full_name": "Shanujan T",
      "bio": "Fresh graduate interested in web development.",
      "location": "Vavuniya",
      "phone": "+94771112233",
      "education_level": "bachelors",
      "resume_url": "https://example.com/resumes/shanujan.pdf",
      "avatar_url": null,
      "is_active": true,
      "created_at": "2026-07-14T10:10:00+00:00"
    },
    {
      "id": 4,
      "email": "priya@localjobs.test",
      "role": "seeker",
      "full_name": "Priya N",
      "bio": "Looking for customer-facing roles.",
      "location": "Jaffna",
      "phone": null,
      "education_level": "diploma",
      "resume_url": "https://example.com/resumes/priya.pdf",
      "avatar_url": null,
      "is_active": true,
      "created_at": "2026-07-14T10:15:00+00:00"
    }
  ],

// COMPANIES
  "companies": [
    {
      "id": 1,
      "owner_id": 2,
      "name": "Vavuniya Tech Solutions",
      "industry": "Technology",
      "description": "Local software and IT support company.",
      "website": "https://vavuniya-tech.example.com",
      "location": "Vavuniya",
      "logo_url": "https://example.com/logos/vts.png",
      "created_at": "2026-07-14T10:20:00+00:00"
    }
  ],

// SKILLS
  "skills": [
    {
      "id": 1,
      "name": "Python",
      "category": "Technology",
      "description": "Programming for web and data.",
      "created_at": "2026-07-14T09:00:00+00:00"
    },
    {
      "id": 2,
      "name": "MySQL",
      "category": "Technology",
      "description": "Relational databases.",
      "created_at": "2026-07-14T09:00:00+00:00"
    },
    {
      "id": 3,
      "name": "JavaScript",
      "category": "Technology",
      "description": "Frontend and scripting.",
      "created_at": "2026-07-14T09:00:00+00:00"
    },
    {
      "id": 4,
      "name": "Customer Service",
      "category": "Business",
      "description": "Front-desk and client support.",
      "created_at": "2026-07-14T09:00:00+00:00"
    },
    {
      "id": 5,
      "name": "English",
      "category": "Language",
      "description": "Spoken and written English.",
      "created_at": "2026-07-14T09:00:00+00:00"
    }
  ],

// USER_SKILLS
  "user_skills": [
    {
      "id": 1,
      "user_id": 3,
      "skill_id": 1,
      "level": "intermediate",
      "skill": {
        "id": 1,
        "name": "Python",
        "category": "Technology",
        "description": "Programming for web and data.",
        "created_at": "2026-07-14T09:00:00+00:00"
      },
      "created_at": "2026-07-14T10:25:00+00:00"
    },
    {
      "id": 2,
      "user_id": 3,
      "skill_id": 2,
      "level": "beginner",
      "skill": {
        "id": 2,
        "name": "MySQL",
        "category": "Technology",
        "description": "Relational databases.",
        "created_at": "2026-07-14T09:00:00+00:00"
      },
      "created_at": "2026-07-14T10:26:00+00:00"
    },
    {
      "id": 3,
      "user_id": 4,
      "skill_id": 4,
      "level": "advanced",
      "skill": {
        "id": 4,
        "name": "Customer Service",
        "category": "Business",
        "description": "Front-desk and client support.",
        "created_at": "2026-07-14T09:00:00+00:00"
      },
      "created_at": "2026-07-14T10:27:00+00:00"
    },
    {
      "id": 4,
      "user_id": 4,
      "skill_id": 5,
      "level": "intermediate",
      "skill": {
        "id": 5,
        "name": "English",
        "category": "Language",
        "description": "Spoken and written English.",
        "created_at": "2026-07-14T09:00:00+00:00"
      },
      "created_at": "2026-07-14T10:28:00+00:00"
    }
  ],

// INTERESTS
  "interests": [
    {
      "id": 1,
      "name": "Web Design",
      "category": "Creative",
      "created_at": "2026-07-14T09:05:00+00:00"
    },
    {
      "id": 2,
      "name": "Career Growth",
      "category": "Business",
      "created_at": "2026-07-14T09:05:00+00:00"
    }
  ],

// USER_INTERESTS
  "user_interests": [
    {
      "id": 1,
      "user_id": 3,
      "interest_id": 1,
      "interest": {
        "id": 1,
        "name": "Web Design",
        "category": "Creative",
        "created_at": "2026-07-14T09:05:00+00:00"
      },
      "created_at": "2026-07-14T10:30:00+00:00"
    },
    {
      "id": 2,
      "user_id": 4,
      "interest_id": 2,
      "interest": {
        "id": 2,
        "name": "Career Growth",
        "category": "Business",
        "created_at": "2026-07-14T09:05:00+00:00"
      },
      "created_at": "2026-07-14T10:31:00+00:00"
    }
  ],

// JOBS
  "jobs": [
    {
      "id": 1,
      "company_id": 1,
      "posted_by": 2,
      "title": "Junior Web Developer",
      "description": "Build and maintain web apps.",
      "category": "Technology",
      "job_type": "full_time",
      "experience_level": "entry",
      "location": "Vavuniya",
      "salary_min": 40000,
      "salary_max": 60000,
      "deadline": "2026-08-31",
      "status": "open",
      "skill_ids": [1, 2],
      "created_at": "2026-07-14T11:00:00+00:00"
    },
    {
      "id": 2,
      "company_id": 1,
      "posted_by": 2,
      "title": "IT Support Intern",
      "description": "Assist the IT team.",
      "category": "Technology",
      "job_type": "internship",
      "experience_level": "entry",
      "location": "Vavuniya",
      "salary_min": null,
      "salary_max": null,
      "deadline": "2026-08-15",
      "status": "open",
      "skill_ids": [3],
      "created_at": "2026-07-14T11:05:00+00:00"
    },
    {
      "id": 3,
      "company_id": 1,
      "posted_by": 2,
      "title": "Front Desk Assistant",
      "description": "Handle front desk and customer inquiries.",
      "category": "Business",
      "job_type": "part_time",
      "experience_level": "entry",
      "location": "Jaffna",
      "salary_min": 25000,
      "salary_max": 35000,
      "deadline": "2026-08-20",
      "status": "open",
      "skill_ids": [4, 5],
      "created_at": "2026-07-14T11:10:00+00:00"
    }
  ],

// JOB_SKILLS
  "job_skills": [
    {
      "id": 1,
      "job_id": 1,
      "skill_id": 1,
      "created_at": "2026-07-14T11:00:00+00:00"
    },
    {
      "id": 2,
      "job_id": 1,
      "skill_id": 2,
      "created_at": "2026-07-14T11:00:00+00:00"
    },
    {
      "id": 3,
      "job_id": 2,
      "skill_id": 3,
      "created_at": "2026-07-14T11:05:00+00:00"
    },
    {
      "id": 4,
      "job_id": 3,
      "skill_id": 4,
      "created_at": "2026-07-14T11:10:00+00:00"
    },
    {
      "id": 5,
      "job_id": 3,
      "skill_id": 5,
      "created_at": "2026-07-14T11:10:00+00:00"
    }
  ],

// APPLICATIONS
  "applications": [
    {
      "id": 1,
      "job_id": 3,
      "seeker_id": 4,
      "cover_letter": "I have strong customer service experience and would love this role.",
      "resume_url": "https://example.com/resumes/priya.pdf",
      "status": "pending",
      "created_at": "2026-07-14T12:00:00+00:00"
    },
    {
      "id": 2,
      "job_id": 1,
      "seeker_id": 3,
      "cover_letter": "My Python and MySQL skills match this junior developer role.",
      "resume_url": "https://example.com/resumes/shanujan.pdf",
      "status": "shortlisted",
      "created_at": "2026-07-14T12:05:00+00:00"
    }
  ],

// POSTS
  "posts": [
    {
      "id": 1,
      "author_id": 2,
      "title": "Hiring Junior Web Developer",
      "body": "We are looking for a junior developer in Vavuniya. Apply via HireHub.",
      "type": "job_share",
      "job_id": 1,
      "created_at": "2026-07-14T13:00:00+00:00"
    },
    {
      "id": 2,
      "author_id": 3,
      "title": "Interview tips for freshers?",
      "body": "What should fresh graduates prepare before local IT interviews?",
      "type": "discussion",
      "job_id": null,
      "created_at": "2026-07-14T13:10:00+00:00"
    }
  ],

// COMMENTS
  "comments": [
    {
      "id": 1,
      "post_id": 2,
      "author_id": 2,
      "body": "Revise your basics, prepare a short project story, and practice English.",
      "created_at": "2026-07-14T13:20:00+00:00"
    }
  ],

// REPORTS
  "reports": [
    {
      "id": 1,
      "reporter_id": 3,
      "target_type": "post",
      "target_id": 1,
      "reason": "spam",
      "details": "Looks like repeated hiring spam.",
      "status": "open",
      "resolved_by": null,
      "created_at": "2026-07-14T14:00:00+00:00"
    }
  ],

// MENTORSHIPS
  "mentorships": [
    {
      "id": 1,
      "mentor_id": 2,
      "mentee_id": 3,
      "status": "requested",
      "message": "Could you mentor me on junior web development careers?",
      "created_at": "2026-07-14T14:30:00+00:00"
    }
  ],

// CONVERSATIONS
  "conversations": [
    {
      "id": 1,
      "participant_one_id": 2,
      "participant_two_id": 3,
      "created_at": "2026-07-14T15:00:00+00:00"
    }
  ],

// MESSAGES
  "messages": [
    {
      "id": 1,
      "conversation_id": 1,
      "sender_id": 3,
      "body": "Hi Kavitha, thanks for the mentoring offer!",
      "is_read": false,
      "created_at": "2026-07-14T15:01:00+00:00"
    },
    {
      "id": 2,
      "conversation_id": 1,
      "sender_id": 2,
      "body": "Happy to help. Let's start with your portfolio.",
      "is_read": false,
      "created_at": "2026-07-14T15:05:00+00:00"
    }
  ],

// SAVED_JOBS
  "saved_jobs": [
    {
      "id": 1,
      "seeker_id": 3,
      "job_id": 1,
      "created_at": "2026-07-14T12:10:00+00:00"
    }
  ],

// NOTIFICATIONS
  "notifications": [
    {
      "id": 1,
      "user_id": 3,
      "type": "application_status",
      "message": "Your application status changed to shortlisted.",
      "link_url": "/applications/2",
      "is_read": false,
      "created_at": "2026-07-14T12:06:00+00:00"
    }
  ],

// AUTH_REQUESTS_EXAMPLES
  "auth_request_examples": {

    "register_seeker": {
      "email": "newseeker@example.com",
      "password": "Seeker123",
      "full_name": "New Seeker",
      "location": "Vavuniya",
      "account_type": "seeker"
    },

    "register_employer": {
      "email": "newemployer@example.com",
      "password": "Employer123",
      "full_name": "New Employer",
      "location": "Vavuniya",
      "role": "employer"
    },
    
    "login": {
      "email": "shanujan@localjobs.test",
      "password": "Seeker123"
    }
  }
}
```
