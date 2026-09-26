from dataclasses import dataclass
import logging

from incident_platform.core.config import get_settings
from incident_platform.integrations.notifications import (
    EmailNotificationProvider,
    LoggingNotificationProvider,
    NotificationMessage,
    NotificationProvider,
    WebhookNotificationProvider,
)
from incident_platform.models.incident import Incident


logger = logging.getLogger(__name__)


ALERT_SEVERITIES = {
    "high",
    "critical",
}


@dataclass(frozen=True)
class NotificationDeliveryResult:
    """Result of an attempted notification delivery."""

    channel: str
    incident_id: int
    success: bool


def should_alert(incident: Incident) -> bool:
    """Return whether an incident severity requires notification."""

    return incident.severity in ALERT_SEVERITIES


def build_notification(incident: Incident) -> NotificationMessage:
    """Build a standardized notification from an incident."""

    return NotificationMessage(
        subject=f"[{incident.severity.upper()}] Incident #{incident.id}: {incident.title}",
        message=(
            f"Incident #{incident.id} requires attention.\n"
            f"Severity: {incident.severity}\n"
            f"Status: {incident.status}\n"
            f"Source: {incident.source}\n"
            f"Description: {incident.description}"
        ),
        severity=incident.severity,
        incident_id=incident.id,
    )


def get_notification_providers() -> list[NotificationProvider]:
    """Build the notification providers enabled by application settings."""

    settings = get_settings()

    providers: list[NotificationProvider] = [
        LoggingNotificationProvider(),
    ]

    if settings.email_notifications_enabled:
        providers.append(EmailNotificationProvider())

    if settings.webhook_notifications_enabled:
        providers.append(WebhookNotificationProvider())

    return providers


def dispatch_alert_with_results(
    incident: Incident,
    providers: list[NotificationProvider] | None = None,
) -> list[NotificationDeliveryResult]:
    """Dispatch an alert and return the result from every provider."""

    if not should_alert(incident):
        return []

    notification = build_notification(incident)

    if providers is None:
        providers = get_notification_providers()

    results: list[NotificationDeliveryResult] = []

    for provider in providers:
        try:
            success = provider.send(notification)

        except Exception:
            logger.exception(
                "Notification provider failed: channel=%s incident_id=%s",
                provider.channel.value,
                incident.id,
            )
            success = False

        result = NotificationDeliveryResult(
            channel=provider.channel.value,
            incident_id=incident.id,
            success=success,
        )

        results.append(result)

        logger.info(
            "Notification delivery: channel=%s incident_id=%s success=%s",
            result.channel,
            result.incident_id,
            result.success,
        )

    return results


def dispatch_alert(
    incident: Incident,
    provider: NotificationProvider | None = None,
) -> bool:
    """Dispatch an alert and return whether at least one delivery succeeded."""

    if provider is not None:
        results = dispatch_alert_with_results(
            incident,
            providers=[provider],
        )
    else:
        results = dispatch_alert_with_results(incident)

    return any(result.success for result in results)
