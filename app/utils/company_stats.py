from app.models import Application, ApplicationStatusLog, Job


def compute_avg_response_time_days(company_id):
    """
    Average days from application submit to first status change away from pending.
    Returns None when fewer than 5 qualifying applications exist.
    """
    app_ids = [
        row[0]
        for row in Application.query.join(Job)
        .filter(Job.company_id == company_id)
        .with_entities(Application.id)
        .all()
    ]
    if not app_ids:
        return None

    deltas = []
    for app_id in app_ids:
        app_row = db.session.get(Application, app_id)
        if not app_row or not app_row.created_at:
            continue
        first_change = (
            ApplicationStatusLog.query.filter_by(application_id=app_id)
            .filter(ApplicationStatusLog.old_status == "pending")
            .filter(ApplicationStatusLog.new_status != "pending")
            .order_by(ApplicationStatusLog.created_at.asc())
            .first()
        )
        if not first_change or not first_change.created_at:
            continue
        delta_days = (first_change.created_at - app_row.created_at).total_seconds() / 86400
        if delta_days >= 0:
            deltas.append(delta_days)

    if len(deltas) < 5:
        return None
    return round(sum(deltas) / len(deltas), 1)
