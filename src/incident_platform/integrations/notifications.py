from dataclasses import dataclass
from email.message import EmailMessage
from enum import StrEnum
import smtplib
from urllib.error import URLError
from urllib.request import Request, urlopen

from incident_platform.core.config import get_settings


class NotificationChannel(StrEnum):
    """Supported notification delivery channels."""

    CONSOLE = "console"
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass(frozen=True)
class NotificationMessage:
    """Standardized notification payload."""

    subject: str
    message: str
    severity: str
    incident_id: int


class NotificationProvider:
    """Base interface for notification providers."""

    channel: NotificationChannel

    def send(self, notification: NotificationMessage) -> bool:
        """Send a notification and return whether delivery succeeded."""

        raise NotImplementedError


class LoggingNotificationProvider(NotificationProvider):
    """Development provider that records notifications locally."""

    channel = NotificationChannel.CONSOLE

    def send(self, notification: NotificationMessage) -> bool:
        """Record a notification through local console output."""

        print(
            "NOTIFICATION",
            {
                "channel": self.channel.value,
                "incident_id": notification.incident_id,
                "severity": notification.severity,
                "subject": notification.subject,
                "message": notification.message,
            },
        )

        return True


class EmailNotificationProvider(NotificationProvider):
    """SMTP-based email notification provider."""

    channel = NotificationChannel.EMAIL

    def send(self, notification: NotificationMessage) -> bool:
        """Send a notification through an SMTP server."""

        settings = get_settings()

        if not settings.email_notifications_enabled:
            return False

        if not settings.smtp_host:
            return False

        if not settings.notification_sender:
            return False

        message = EmailMessage()
        message["Subject"] = notification.subject
        message["From"] = settings.notification_sender
        message["To"] = settings.notification_sender
        message.set_content(notification.message)

        try:
            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=10,
            ) as smtp:
                smtp.starttls()

                if settings.smtp_username and settings.smtp_password:
                    smtp.login(
                        settings.smtp_username,
                        settings.smtp_password,
                    )

                smtp.send_message(message)

        except (OSError, smtplib.SMTPException):
            return False

        return True


class WebhookNotificationProvider(NotificationProvider):
    """HTTP webhook notification provider."""

    channel = NotificationChannel.WEBHOOK

    def send(self, notification: NotificationMessage) -> bool:
        """Send a notification to a configured HTTP webhook."""

        settings = get_settings()

        if not settings.webhook_notifications_enabled:
            return False

        if not settings.webhook_url:
            return False

        payload = (
            "{"
            f'"incident_id": {notification.incident_id}, '
            f'"severity": "{notification.severity}", '
            f'"subject": "{_escape_json(notification.subject)}", '
            f'"message": "{_escape_json(notification.message)}"'
            "}"
        ).encode("utf-8")

        request = Request(
            settings.webhook_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=10) as response:
                return 200 <= response.status < 300

        except (OSError, URLError):
            return False


def _escape_json(value: str) -> str:
    """Escape a string for use inside a JSON payload."""

    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
