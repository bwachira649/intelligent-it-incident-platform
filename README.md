# Intelligent IT Incident & Alert Management Platform

A professional Python-based incident management platform for recording operational incidents, managing their lifecycle, dispatching alerts, maintaining an audit trail, and providing a browser-based operational dashboard backed by a REST API.

The platform is designed around practical IT operations workflows and demonstrates API development, database persistence, notification integrations, event tracking, automated testing, and operational monitoring.

## Project Status

**Core platform implemented and tested.**

The current implementation provides an end-to-end incident workflow:

**Create → Notify → Acknowledge → Resolve → Audit**

Automated tests currently cover the API and notification subsystems with:

    25 tests passed
    0 failures
    0 warnings

## Key Features

### Incident Management

- Create incidents through the REST API or operational dashboard
- Classify incidents by severity:
  - Low
  - Medium
  - High
  - Critical
- Track incident status:
  - Open
  - Acknowledged
  - Resolved
- Record creation, acknowledgement, and resolution timestamps
- Retrieve individual incidents and incident collections
- Update incident information through the API

### Operational Dashboard

The browser-based dashboard provides:

- Total incident count
- Open incident count
- Acknowledged incident count
- Resolved incident count
- Severity distribution
- System health status
- API operational status
- Recent incident list
- Incident detail view
- Incident event history
- Incident creation form
- Incident acknowledgement and resolution controls

### Notifications

The notification subsystem supports a provider-based architecture for:

- Console/log notifications
- Email notifications
- Webhook notifications
- Notification success and failure tracking
- Severity-based alert decisions
- Multiple notification providers

High and critical incidents can trigger alert delivery according to the configured notification providers.

### Audit & Event History

Incident lifecycle actions are recorded as events.

Example event sequence:

    incident_created
    notification_sent
    incident_acknowledged
    incident_resolved

This provides an auditable history of operational actions associated with an incident.

### REST API

The platform exposes versioned REST endpoints for:

- Incident creation
- Incident listing
- Incident retrieval
- Incident updates
- Incident acknowledgement
- Incident resolution
- Incident statistics
- Incident event history
- Service health
- Application status

API documentation is available automatically through FastAPI when the application is running.

## Architecture

The project follows a layered application structure:

    Browser Dashboard
           │
           ▼
       FastAPI API
           │
           ▼
      Service Layer
           │
     ┌─────┼──────────────┐
     ▼     ▼              ▼
    Database  Notifications  Event Tracking
     │         │              │
     ▼         ▼              ▼
    SQLite    Console       Incident Events
              Email
              Webhook

### Project Structure

    intelligent-it-incident-platform/
    │
    ├── src/
    │   └── incident_platform/
    │       ├── api/
    │       │   └── incidents.py
    │       │
    │       ├── core/
    │       │   └── config.py
    │       │
    │       ├── db/
    │       │   └── database.py
    │       │
    │       ├── integrations/
    │       │   └── notifications.py
    │       │
    │       ├── models/
    │       │   ├── incident.py
    │       │   └── incident_event.py
    │       │
    │       ├── schemas/
    │       │   └── incident.py
    │       │
    │       ├── services/
    │       │   ├── alerts.py
    │       │   ├── events.py
    │       │   ├── incidents.py
    │       │   └── statistics.py
    │       │
    │       ├── web/
    │       │   ├── index.html
    │       │   ├── router.py
    │       │   └── static/
    │       │       ├── app.js
    │       │       └── style.css
    │       │
    │       └── main.py
    │
    ├── tests/
    │   ├── test_api_incidents.py
    │   └── test_notifications.py
    │
    ├── logs/
    ├── reports/
    ├── .env.example
    ├── .gitignore
    ├── pyproject.toml
    └── README.md

## REST API

Base API path:

    /api/v1/incidents

### Health

    GET /health

Returns the service health status.

### Application Status

    GET /

Returns application name, version, environment, and operational status.

### List Incidents

    GET /api/v1/incidents

Returns persisted incidents.

### Create Incident

    POST /api/v1/incidents

Example request:

    {
      "title": "Database connectivity failure",
      "description": "Production application cannot connect to the database.",
      "severity": "critical",
      "source": "database-monitor"
    }

### Get Incident

    GET /api/v1/incidents/{incident_id}

### Update Incident

    PATCH /api/v1/incidents/{incident_id}

### Acknowledge Incident

    POST /api/v1/incidents/{incident_id}/acknowledge

### Resolve Incident

    POST /api/v1/incidents/{incident_id}/resolve

### Incident Statistics

    GET /api/v1/incidents/statistics

### Incident Event History

    GET /api/v1/incidents/{incident_id}/events

## Dashboard

The operational dashboard is available at:

    http://127.0.0.1:8000/dashboard

The dashboard communicates with the REST API directly and provides an interactive interface for managing incidents.

## Installation

### Requirements

- Python 3.11+
- Git

The application uses SQLite by default, so no external database server is required for local development.

### Clone the Repository

    git clone https://github.com/bwachira649/intelligent-it-incident-platform.git
    cd intelligent-it-incident-platform

### Create a Virtual Environment

#### Linux / macOS

    python3 -m venv .venv
    source .venv/bin/activate

#### Windows Command Prompt

    python -m venv .venv
    .venv\Scripts\activate

#### Windows PowerShell

    python -m venv .venv
    .venv\Scripts\Activate.ps1

### Install the Project

    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"

## Configuration

Copy the example environment file.

### Linux / macOS

    cp .env.example .env

### Windows Command Prompt

    copy .env.example .env

### Windows PowerShell

    Copy-Item .env.example .env

The application uses environment variables for configuration such as:

- Application environment
- API host and port
- Database URL
- Log level
- Default incident severity
- Email notification settings
- Webhook notification settings

Notification providers that are not configured remain disabled.

## Running the Application

Start the development server with:

    python -m incident_platform.main

The default server runs at:

    http://127.0.0.1:8000

Open the operational dashboard:

    http://127.0.0.1:8000/dashboard

FastAPI interactive API documentation:

    http://127.0.0.1:8000/docs

Alternative OpenAPI documentation:

    http://127.0.0.1:8000/redoc

## Testing

Run the complete automated test suite:

    python -m pytest

The test suite covers:

- Health endpoint
- Application status endpoint
- Incident creation
- Incident retrieval
- Incident listing
- Incident statistics
- Incident event history
- Incident acknowledgement
- Incident resolution
- Complete incident lifecycle
- 404 handling
- Notification provider behavior
- Alert severity decisions
- Email notification behavior
- Webhook notification behavior
- Notification failure handling
- Multiple notification providers

API mutation tests use isolated temporary SQLite databases so automated testing does not modify the local development database.

## Verification Evidence

The platform has been manually verified through the operational dashboard and REST API.

A complete incident lifecycle was successfully demonstrated:

    1. Create Incident
           ↓
    2. Incident Stored in SQLite
           ↓
    3. Notification Sent
           ↓
    4. Incident Acknowledged
           ↓
    5. Incident Resolved
           ↓
    6. Event History Updated
           ↓
    7. Dashboard Statistics Updated

The verified dashboard workflow included:

- Creating a high-severity incident
- Automatically selecting the created incident
- Recording the notification event
- Acknowledging the incident
- Resolving the incident
- Updating dashboard statistics
- Displaying the complete event history

The REST API was also independently verified for:

- Health status
- Application status
- Incident listing
- Individual incident retrieval
- Statistics
- Event history
- Controlled 404 responses

## Project Screenshots

Screenshots demonstrating the working dashboard will be stored in:

    docs/images/

Planned evidence includes:

- Operational dashboard overview
- Incident creation
- Incident details
- Incident acknowledgement
- Incident resolution
- Event history
- API documentation

## Video / GUI Demonstration

A short demonstration video will document the main operational workflow:

    Create Incident
           ↓
    Notification
           ↓
    Acknowledge
           ↓
    Resolve
           ↓
    Review Event History

Demonstration videos will be stored in:

    docs/videos/

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11+ | Application development |
| FastAPI | REST API framework |
| Uvicorn | ASGI application server |
| SQLAlchemy | Database access and ORM |
| SQLite | Local persistent storage |
| Pydantic | Data validation and schemas |
| Pydantic Settings | Environment-based configuration |
| HTML/CSS/JavaScript | Operational dashboard |
| HTTPX | API and integration testing |
| Pytest | Automated testing |

## Engineering Practices Demonstrated

This project demonstrates practical experience with:

- Python application architecture
- REST API development
- FastAPI
- SQLAlchemy ORM
- SQLite persistence
- Pydantic validation
- Service-layer architecture
- Dependency injection
- Environment-based configuration
- Notification provider architecture
- Webhook integration design
- Event-driven audit tracking
- Incident lifecycle management
- Automated API testing
- Isolated test databases
- Error handling
- Health checks
- Operational dashboards
- Git version control
- Cross-platform development practices

## Security & Configuration

Sensitive configuration values are intentionally excluded from version control.

The repository includes:

    .env.example

while local:

    .env

is ignored by Git.

Database files, logs, generated reports, virtual environments, and Python cache files are also excluded from version control.

## Development Workflow

The project follows a practical development workflow:

    Design
      ↓
    Implement
      ↓
    Test
      ↓
    Manual Verification
      ↓
    Capture Evidence
      ↓
    Document
      ↓
    Cross-Platform Verification
      ↓
    Publish

## Future Extension Areas

The architecture provides room for future operational integrations such as:

- Additional notification providers
- External monitoring integrations
- Authentication and role-based access control
- Advanced incident filtering
- Reporting and analytics
- Scheduled automation
- External webhook consumers
- Containerized deployment
- Production database backends
- Cloud deployment

These are extension areas rather than requirements for the current local implementation.

## License

This project is released under the MIT License.
