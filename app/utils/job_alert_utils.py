from app.models import SavedSearch


def find_matching_saved_searches(job):
    """
    Return SavedSearch rows whose criteria match the given Job.
    Intended for wiring job-alert notifications when a new job is posted.
    """
    query = SavedSearch.query
    rows = query.all()
    matches = []

    for search in rows:
        if search.keywords:
            kw = search.keywords.strip().lower()
            title = (job.title or "").lower()
            description = (job.description or "").lower()
            if kw not in title and kw not in description:
                continue

        if search.category:
            job_category = (job.category or "").lower()
            if search.category.strip().lower() not in job_category:
                continue

        if search.location:
            job_location = (job.location or "").lower()
            if search.location.strip().lower() not in job_location:
                continue

        if search.job_type:
            if (job.job_type or "").lower() != search.job_type.strip().lower():
                continue

        if search.min_salary is not None:
            job_salary = job.salary_max if job.salary_max is not None else job.salary_min
            if job_salary is None or job_salary < search.min_salary:
                continue

        matches.append(search)

    return matches
