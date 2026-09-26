from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from incident_platform.db.database import Base, get_db
from incident_platform.main import app
from incident_platform.models.incident import Incident
from incident_platform.models.incident_event import IncidentEvent


@pytest_asyncio.fixture
async def api_client(tmp_path: Path):
    """Provide an isolated HTTP client backed by a temporary SQLite database."""

    database_path = tmp_path / "test_incident_platform.db"

    test_engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )

    TestSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        """Provide an isolated database session for the test."""

        db = TestSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.mark.asyncio
async def test_health_endpoint(api_client):
    """Health endpoint should report a healthy service."""

    response = await api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_root_endpoint(api_client):
    """Root endpoint should expose application status information."""

    response = await api_client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Intelligent IT Incident & Alert Management Platform"
    assert data["version"] == "0.1.0"
    assert data["status"] == "operational"


@pytest.mark.asyncio
async def test_list_incidents(api_client):
    """Incident listing endpoint should return persisted incidents."""

    response = await api_client.get("/api/v1/incidents")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert data == []


@pytest.mark.asyncio
async def test_create_incident(api_client):
    """The API should create a new incident successfully."""

    payload = {
        "title": "API creation test",
        "description": "Testing incident creation through the REST API.",
        "severity": "high",
        "source": "api-test",
    }

    response = await api_client.post(
        "/api/v1/incidents",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["title"] == "API creation test"
    assert data["description"] == (
        "Testing incident creation through the REST API."
    )
    assert data["severity"] == "high"
    assert data["status"] == "open"
    assert data["source"] == "api-test"
    assert data["acknowledged_at"] is None
    assert data["resolved_at"] is None


@pytest.mark.asyncio
async def test_get_created_incident(api_client):
    """The API should return an incident after it has been created."""

    payload = {
        "title": "Retrieve test incident",
        "description": "Testing retrieval of a newly created incident.",
        "severity": "medium",
        "source": "api-test",
    }

    create_response = await api_client.post(
        "/api/v1/incidents",
        json=payload,
    )

    assert create_response.status_code == 201

    incident_id = create_response.json()["id"]

    response = await api_client.get(
        f"/api/v1/incidents/{incident_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == incident_id
    assert data["title"] == "Retrieve test incident"
    assert data["status"] == "open"


@pytest.mark.asyncio
async def test_incident_statistics(api_client):
    """Statistics endpoint should reflect incidents created during the test."""

    incidents = [
        {
            "title": "Open incident",
            "description": "Testing an open incident.",
            "severity": "critical",
            "source": "statistics-test",
        },
        {
            "title": "Second open incident",
            "description": "Testing a second open incident.",
            "severity": "high",
            "source": "statistics-test",
        },
    ]

    for payload in incidents:
        response = await api_client.post(
            "/api/v1/incidents",
            json=payload,
        )

        assert response.status_code == 201

    response = await api_client.get(
        "/api/v1/incidents/statistics"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert data["open"] == 2
    assert data["acknowledged"] == 0
    assert data["resolved"] == 0
    assert data["critical"] == 1
    assert data["high"] == 1


@pytest.mark.asyncio
async def test_incident_event_history(api_client):
    """Creating an incident should record its creation and notification events."""

    payload = {
        "title": "Event history test",
        "description": "Testing incident audit events.",
        "severity": "critical",
        "source": "event-test",
    }

    create_response = await api_client.post(
        "/api/v1/incidents",
        json=payload,
    )

    assert create_response.status_code == 201

    incident_id = create_response.json()["id"]

    response = await api_client.get(
        f"/api/v1/incidents/{incident_id}/events"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    event_types = [event["event_type"] for event in data]

    assert event_types == [
        "incident_created",
        "notification_sent",
    ]


@pytest.mark.asyncio
async def test_acknowledge_incident(api_client):
    """The API should acknowledge an open incident."""

    payload = {
        "title": "Acknowledgement test",
        "description": "Testing incident acknowledgement.",
        "severity": "high",
        "source": "lifecycle-test",
    }

    create_response = await api_client.post(
        "/api/v1/incidents",
        json=payload,
    )

    assert create_response.status_code == 201

    incident_id = create_response.json()["id"]

    response = await api_client.post(
        f"/api/v1/incidents/{incident_id}/acknowledge"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == incident_id
    assert data["status"] == "acknowledged"
    assert data["acknowledged_at"] is not None
    assert data["resolved_at"] is None


@pytest.mark.asyncio
async def test_resolve_incident(api_client):
    """The API should resolve an incident."""

    payload = {
        "title": "Resolution test",
        "description": "Testing incident resolution.",
        "severity": "critical",
        "source": "lifecycle-test",
    }

    create_response = await api_client.post(
        "/api/v1/incidents",
        json=payload,
    )

    assert create_response.status_code == 201

    incident_id = create_response.json()["id"]

    response = await api_client.post(
        f"/api/v1/incidents/{incident_id}/resolve"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == incident_id
    assert data["status"] == "resolved"
    assert data["resolved_at"] is not None


@pytest.mark.asyncio
async def test_complete_incident_lifecycle(api_client):
    """The API should support create, acknowledge, resolve, and audit history."""

    payload = {
        "title": "Complete lifecycle test",
        "description": "Testing the complete incident lifecycle.",
        "severity": "critical",
        "source": "lifecycle-test",
    }

    create_response = await api_client.post(
        "/api/v1/incidents",
        json=payload,
    )

    assert create_response.status_code == 201

    incident_id = create_response.json()["id"]

    acknowledge_response = await api_client.post(
        f"/api/v1/incidents/{incident_id}/acknowledge"
    )

    assert acknowledge_response.status_code == 200
    assert acknowledge_response.json()["status"] == "acknowledged"

    resolve_response = await api_client.post(
        f"/api/v1/incidents/{incident_id}/resolve"
    )

    assert resolve_response.status_code == 200
    assert resolve_response.json()["status"] == "resolved"

    incident_response = await api_client.get(
        f"/api/v1/incidents/{incident_id}"
    )

    assert incident_response.status_code == 200

    incident = incident_response.json()

    assert incident["status"] == "resolved"
    assert incident["acknowledged_at"] is not None
    assert incident["resolved_at"] is not None

    events_response = await api_client.get(
        f"/api/v1/incidents/{incident_id}/events"
    )

    assert events_response.status_code == 200

    events = events_response.json()

    event_types = [event["event_type"] for event in events]

    assert event_types == [
        "incident_created",
        "notification_sent",
        "incident_acknowledged",
        "incident_resolved",
    ]


@pytest.mark.asyncio
async def test_missing_incident_returns_404(api_client):
    """Unknown incident IDs should return a controlled 404 response."""

    response = await api_client.get(
        "/api/v1/incidents/99999"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Incident 99999 not found."
    }
