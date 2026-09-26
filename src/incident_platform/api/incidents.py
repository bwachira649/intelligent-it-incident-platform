from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from incident_platform.db.database import get_db
from incident_platform.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
)
from incident_platform.services.events import list_events
from incident_platform.services.incidents import (
    acknowledge_incident,
    create_incident,
    get_incident,
    list_incidents,
    resolve_incident,
    update_incident,
)
from incident_platform.services.statistics import get_incident_statistics

router = APIRouter(
    prefix="/api/v1/incidents",
    tags=["Incidents"],
)


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_incident_endpoint(
    incident_data: IncidentCreate,
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """Create a new incident."""

    return create_incident(db, incident_data)


@router.get(
    "",
    response_model=list[IncidentResponse],
)
def list_incidents_endpoint(
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
    severity: str | None = None,
    db: Session = Depends(get_db),
) -> list[IncidentResponse]:
    """List incidents with optional filters."""

    return list_incidents(
        db,
        status=status_filter,
        severity=severity,
    )


@router.get(
    "/statistics",
)
def incident_statistics_endpoint(
    db: Session = Depends(get_db),
) -> dict[str, int]:
    """Return aggregated incident statistics for the dashboard."""

    return get_incident_statistics(db)


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
)
def get_incident_endpoint(
    incident_id: int,
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """Return one incident by ID."""

    incident = get_incident(db, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found.",
        )

    return incident


@router.get(
    "/{incident_id}/events",
)
def list_incident_events_endpoint(
    incident_id: int,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Return the audit history for an incident."""

    incident = get_incident(db, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found.",
        )

    events = list_events(db, incident_id)

    return [
        {
            "id": event.id,
            "incident_id": event.incident_id,
            "event_type": event.event_type,
            "description": event.description,
            "created_at": event.created_at,
        }
        for event in events
    ]


@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
)
def update_incident_endpoint(
    incident_id: int,
    incident_data: IncidentUpdate,
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """Update an existing incident."""

    incident = get_incident(db, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found.",
        )

    return update_incident(db, incident, incident_data)


@router.post(
    "/{incident_id}/acknowledge",
    response_model=IncidentResponse,
)
def acknowledge_incident_endpoint(
    incident_id: int,
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """Acknowledge an incident."""

    incident = get_incident(db, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found.",
        )

    try:
        return acknowledge_incident(db, incident)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{incident_id}/resolve",
    response_model=IncidentResponse,
)
def resolve_incident_endpoint(
    incident_id: int,
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """Resolve an incident."""

    incident = get_incident(db, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found.",
        )

    try:
        return resolve_incident(db, incident)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
