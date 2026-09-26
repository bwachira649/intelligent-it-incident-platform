from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Intelligent IT Incident & Alert Management Platform"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)

    database_url: str = "sqlite:///./incident_platform.db"

    log_level: str = "INFO"

    incident_default_severity: str = "medium"

    email_notifications_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = ""
    smtp_password: str = ""
    notification_sender: str = ""

    webhook_notifications_enabled: bool = False
    webhook_url: str = ""

    @property
    def is_production(self) -> bool:
        """Return whether the application is running in production."""
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
