"""Profile completion score, onboarding checklist, and milestone badges for seekers."""

ONBOARDING_CHECKLIST = [
    {
        "key": "has_skills",
        "label": "Add your first skill",
        "href": "/my/skills/new",
    },
    {
        "key": "has_resume",
        "label": "Upload your resume",
        "href": "/profile",
    },
    {
        "key": "has_community",
        "label": "Join a community",
        "href": "/communities",
    },
    {
        "key": "has_application",
        "label": "Apply to your first job",
        "href": "/jobs",
    },
    {
        "key": "has_verified_skill",
        "label": "Get a skill verified",
        "href": "/my/skills",
    },
]


def compute_profile_completion(user, skills=None, applications_count=0, community_count=0):
    """
    Return profile_completion_score (0–100), badges, and onboarding checklist.
    Score uses five equal-weight criteria (20% each).
    """
    skills = skills if skills is not None else list(getattr(user, "skills", []) or [])
    checks = {
        "has_skills": len(skills) > 0,
        "has_resume": bool(getattr(user, "resume_url", None)),
        "has_verified_skill": any(getattr(s, "verified", False) for s in skills),
        "has_community": community_count > 0,
        "has_application": applications_count > 0,
    }
    total = len(checks)
    completed = sum(1 for v in checks.values() if v)
    score = round((completed / total) * 100) if total else 0

    checklist = [
        {
            **item,
            "completed": checks[item["key"]],
        }
        for item in ONBOARDING_CHECKLIST
    ]

    badges = []
    if score >= 100:
        badges.append("Profile complete")
    if checks["has_application"]:
        badges.append("First application")
    if checks["has_verified_skill"]:
        badges.append("Skill verified")
    if checks["has_community"]:
        badges.append("Community member")

    return score, badges, checklist
