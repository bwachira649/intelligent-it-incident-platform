from sqlalchemy import select
from sqlalchemy.orm import Session

from incident_platform.models.incident_event import IncidentEvent


class IncidentEventType:
    """Supported incident event types."""

    CREATED = "incident_created"
    UPDATED = "incident_updated"
    ACKNOWLEDGED = "incident_acknowledged"
    RESOLVED = "incident_resolved"
    NOTIFICATION_SENT = "notification_sent"
    NOTIFICATION_FAILED = "notification_failed"


def record_event(
    db: Session,
    incident_id: int,
    event_type: str,
    description: str,
) -> IncidentEvent:
    """Record an event in an incident's history."""

    event = IncidentEvent(
        incident_id=incident_id,
        event_type=event_type,
        description=description,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


def list_events(
    db: Session,
    incident_id: int,
) -> list[IncidentEvent]:
    """Return an incident's events in chronological order."""

    statement = (
        select(IncidentEvent)
        .where(IncidentEvent.incident_id == incident_id)
        .order_by(IncidentEvent.created_at.asc())
    )

    return list(db.scalars(statement).all())
