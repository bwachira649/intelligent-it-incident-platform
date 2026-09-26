from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class IncidentSeverity(StrEnum):
    """Supported incident severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(StrEnum):
    """Supported incident lifecycle states."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class IncidentCreate(BaseModel):
    """Data required to create an incident."""

    title: str = Field(
        min_length=3,
        max_length=200,
    )

    description: str = Field(
        min_length=3,
    )

    severity: IncidentSeverity = Field(
        default=IncidentSeverity.MEDIUM,
    )

    source: str = Field(
        min_length=2,
        max_length=100,
    )


class IncidentUpdate(BaseModel):
    """Data that can be changed on an existing incident."""

    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        min_length=3,
    )

    severity: IncidentSeverity | None = Field(
        default=None,
    )


class IncidentResponse(BaseModel):
    """API representation of an incident."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    source: str
    created_at: datetime
    updated_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
