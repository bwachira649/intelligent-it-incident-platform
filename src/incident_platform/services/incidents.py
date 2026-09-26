from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from incident_platform.integrations.notifications import NotificationProvider
from incident_platform.models.incident import Incident
from incident_platform.schemas.incident import (
    IncidentCreate,
    IncidentStatus,
    IncidentUpdate,
)
from incident_platform.services.alerts import dispatch_alert_with_results
from incident_platform.services.events import IncidentEventType, record_event


def create_incident(
    db: Session,
    incident_data: IncidentCreate,
    notification_provider: NotificationProvider | None = None,
) -> Incident:
    """Create an incident and record its initial lifecycle event."""

    incident = Incident(
        title=incident_data.title,
        description=incident_data.description,
        severity=incident_data.severity.value,
        source=incident_data.source,
        status=IncidentStatus.OPEN.value,
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    record_event(
        db,
        incident.id,
        IncidentEventType.CREATED,
        f"Incident created from source '{incident.source}'.",
    )

    results = dispatch_alert_with_results(
        incident,
        providers=(
            [notification_provider]
            if notification_provider is not None
            else None
        ),
    )

    for result in results:
        event_type = (
            IncidentEventType.NOTIFICATION_SENT
            if result.success
            else IncidentEventType.NOTIFICATION_FAILED
        )

        status = "succeeded" if result.success else "failed"

        record_event(
            db,
            incident.id,
            event_type,
            (
                f"Notification delivery {status} through "
                f"{result.channel}."
            ),
        )

    return incident


def get_incident(
    db: Session,
    incident_id: int,
) -> Incident | None:
    """Return an incident by ID."""

    statement = select(Incident).where(Incident.id == incident_id)

    return db.scalar(statement)


def list_incidents(
    db: Session,
    status: str | None = None,
    severity: str | None = None,
) -> list[Incident]:
    """Return incidents with optional status and severity filters."""

    statement = select(Incident).order_by(Incident.created_at.desc())

    if status:
        statement = statement.where(Incident.status == status)

    if severity:
        statement = statement.where(Incident.severity == severity)

    return list(db.scalars(statement).all())


def update_incident(
    db: Session,
    incident: Incident,
    incident_data: IncidentUpdate,
) -> Incident:
    """Update editable incident fields."""

    updates = incident_data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    for field, value in updates.items():
        if field == "severity":
            value = value.value

        setattr(incident, field, value)

    incident.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(incident)

    record_event(
        db,
        incident.id,
        IncidentEventType.UPDATED,
        "Incident details were updated.",
    )

    return incident


def acknowledge_incident(
    db: Session,
    incident: Incident,
) -> Incident:
    """Acknowledge an open incident."""

    if incident.status == IncidentStatus.RESOLVED.value:
        raise ValueError("A resolved incident cannot be acknowledged.")

    incident.status = IncidentStatus.ACKNOWLEDGED.value
    incident.acknowledged_at = datetime.now(timezone.utc)
    incident.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(incident)

    record_event(
        db,
        incident.id,
        IncidentEventType.ACKNOWLEDGED,
        "Incident was acknowledged by an operator.",
    )

    return incident


def resolve_incident(
    db: Session,
    incident: Incident,
) -> Incident:
    """Resolve an incident."""

    if incident.status == IncidentStatus.RESOLVED.value:
        raise ValueError("Incident is already resolved.")

    incident.status = IncidentStatus.RESOLVED.value
    incident.resolved_at = datetime.now(timezone.utc)
    incident.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(incident)

    record_event(
        db,
        incident.id,
        IncidentEventType.RESOLVED,
        "Incident was resolved by an operator.",
    )

    return incident
