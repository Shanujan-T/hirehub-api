"""Profile completion score and milestone badges for seekers."""


def compute_profile_completion(user, skills=None, applications_count=0, community_count=0):
    """
    Return profile_completion_score (0–100) and earned badge labels.
    All inputs are optional/gracefully degrading.
    """
    skills = skills if skills is not None else list(getattr(user, "skills", []) or [])
    checks = {
        "has_skills": len(skills) > 0,
        "has_resume": bool(getattr(user, "resume_url", None)),
        "has_verified_skill": any(getattr(s, "verified", False) for s in skills),
        "has_community": community_count > 0,
        "has_application": applications_count > 0,
        "has_location": bool(getattr(user, "location", None)),
        "has_bio": bool(getattr(user, "bio", None)),
    }
    total = len(checks)
    completed = sum(1 for v in checks.values() if v)
    score = round((completed / total) * 100) if total else 0

    badges = []
    if score >= 100:
        badges.append("Profile complete")
    if checks["has_application"]:
        badges.append("First application")
    if checks["has_verified_skill"]:
        badges.append("Skill verified")
    if checks["has_community"]:
        badges.append("Community member")

    return score, badges
