from sqlalchemy import func, select
from sqlalchemy.orm import Session

from incident_platform.models.incident import Incident


def get_incident_statistics(db: Session) -> dict[str, int]:
    """Return aggregated incident statistics."""

    total = db.scalar(
        select(func.count()).select_from(Incident)
    ) or 0

    open_count = db.scalar(
        select(func.count())
        .select_from(Incident)
        .where(Incident.status == "open")
    ) or 0

    acknowledged_count = db.scalar(
        select(func.count())
        .select_from(Incident)
        .where(Incident.status == "acknowledged")
    ) or 0

    resolved_count = db.scalar(
        select(func.count())
        .select_from(Incident)
        .where(Incident.status == "resolved")
    ) or 0

    low_count = db.scalar(
        select(func.count())
        .select_from(Incident)
        .where(Incident.severity == "low")
    ) or 0

    medium_count = db.scalar(
        select(func.count())
        .select_from(Incident)
        .where(Incident.severity == "medium")
    ) or 0

    high_count = db.scalar(
        select(func.count())
        .select_from(Incident)
        .where(Incident.severity == "high")
    ) or 0

    critical_count = db.scalar(
        select(func.count())
        .select_from(Incident)
        .where(Incident.severity == "critical")
    ) or 0

    return {
        "total": total,
        "open": open_count,
        "acknowledged": acknowledged_count,
        "resolved": resolved_count,
        "low": low_count,
        "medium": medium_count,
        "high": high_count,
        "critical": critical_count,
    }
