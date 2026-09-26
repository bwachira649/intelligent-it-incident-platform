from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from incident_platform.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


def _create_engine():
    """Create the SQLAlchemy engine using application settings."""
    settings = get_settings()

    connect_args = {}

    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        settings.database_url,
        connect_args=connect_args,
        future=True,
    )


engine = _create_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Provide a database session and close it after use."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all registered database tables."""
    Base.metadata.create_all(bind=engine)
