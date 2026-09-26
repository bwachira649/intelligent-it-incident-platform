from contextlib import asynccontextmanager

from fastapi import FastAPI

from incident_platform.api.incidents import router as incidents_router
from incident_platform.core.config import get_settings
from incident_platform.db.database import init_db
from incident_platform.models import Incident, IncidentEvent
from incident_platform.web.router import router as web_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application resources during startup."""

    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Incident management and alerting platform for "
        "operational events, notifications, integrations, and reporting."
    ),
    lifespan=lifespan,
)


@app.get(
    "/",
    tags=["System"],
)
def root() -> dict[str, str]:
    """Return basic application information."""

    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "operational",
    }


@app.get(
    "/health",
    tags=["System"],
)
def health_check() -> dict[str, str]:
    """Return the application health status."""

    return {
        "status": "healthy",
    }


app.include_router(incidents_router)
app.include_router(web_router)


def main() -> None:
    """Start the development server."""

    import uvicorn

    uvicorn.run(
        "incident_platform.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
