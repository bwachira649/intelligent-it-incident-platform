from unittest.mock import MagicMock, patch

from incident_platform.integrations.notifications import (
    EmailNotificationProvider,
    LoggingNotificationProvider,
    NotificationChannel,
    NotificationMessage,
    NotificationProvider,
    WebhookNotificationProvider,
)
from incident_platform.models.incident import Incident
from incident_platform.services.alerts import (
    build_notification,
    dispatch_alert,
    dispatch_alert_with_results,
    should_alert,
)


def make_notification() -> NotificationMessage:
    """Create a reusable notification for tests."""

    return NotificationMessage(
        subject="[CRITICAL] Incident #100: Database unavailable",
        message="The production database is unavailable.",
        severity="critical",
        incident_id=100,
    )


def make_incident(
    severity: str = "critical",
    incident_id: int = 100,
) -> Incident:
    """Create an in-memory incident for alert tests."""

    return Incident(
        id=incident_id,
        title="Database unavailable",
        description="The production database is unavailable.",
        severity=severity,
        status="open",
        source="health-check",
    )


def test_notification_message_contains_required_fields():
    """Notification messages should retain their core incident data."""

    notification = make_notification()

    assert notification.incident_id == 100
    assert notification.severity == "critical"
    assert notification.subject.startswith("[CRITICAL]")
    assert "database" in notification.message.lower()


def test_logging_provider_sends_notification(capsys):
    """The console provider should record notifications successfully."""

    provider = LoggingNotificationProvider()

    result = provider.send(make_notification())

    captured = capsys.readouterr()

    assert result is True
    assert provider.channel == NotificationChannel.CONSOLE
    assert "NOTIFICATION" in captured.out
    assert "incident_id" in captured.out
    assert "100" in captured.out


def test_email_provider_returns_false_when_disabled():
    """Email delivery should be skipped when disabled."""

    provider = EmailNotificationProvider()

    with patch(
        "incident_platform.integrations.notifications.get_settings"
    ) as mock_settings:
        mock_settings.return_value.email_notifications_enabled = False

        result = provider.send(make_notification())

    assert result is False


def test_webhook_provider_returns_false_when_disabled():
    """Webhook delivery should be skipped when disabled."""

    provider = WebhookNotificationProvider()

    with patch(
        "incident_platform.integrations.notifications.get_settings"
    ) as mock_settings:
        mock_settings.return_value.webhook_notifications_enabled = False

        result = provider.send(make_notification())

    assert result is False


def test_email_provider_sends_message():
    """Email provider should send through the configured SMTP server."""

    provider = EmailNotificationProvider()

    settings = MagicMock()
    settings.email_notifications_enabled = True
    settings.smtp_host = "smtp.example.com"
    settings.smtp_port = 587
    settings.notification_sender = "alerts@example.com"
    settings.smtp_username = "alerts@example.com"
    settings.smtp_password = "test-password"

    with (
        patch(
            "incident_platform.integrations.notifications.get_settings",
            return_value=settings,
        ),
        patch(
            "incident_platform.integrations.notifications.smtplib.SMTP"
        ) as mock_smtp,
    ):
        smtp_connection = mock_smtp.return_value.__enter__.return_value

        result = provider.send(make_notification())

    assert result is True
    mock_smtp.assert_called_once_with(
        "smtp.example.com",
        587,
        timeout=10,
    )
    smtp_connection.starttls.assert_called_once()
    smtp_connection.login.assert_called_once_with(
        "alerts@example.com",
        "test-password",
    )
    smtp_connection.send_message.assert_called_once()


def test_webhook_provider_sends_payload():
    """Webhook provider should send an HTTP POST request."""

    provider = WebhookNotificationProvider()

    settings = MagicMock()
    settings.webhook_notifications_enabled = True
    settings.webhook_url = "https://example.com/webhook"

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__enter__.return_value = mock_response

    with (
        patch(
            "incident_platform.integrations.notifications.get_settings",
            return_value=settings,
        ),
        patch(
            "incident_platform.integrations.notifications.urlopen",
            return_value=mock_response,
        ) as mock_urlopen,
    ):
        result = provider.send(make_notification())

    assert result is True
    mock_urlopen.assert_called_once()

    request = mock_urlopen.call_args.args[0]

    assert request.full_url == "https://example.com/webhook"
    assert request.method == "POST"
    assert request.get_header("Content-type") == "application/json"


def test_should_alert_for_high_and_critical():
    """High and critical incidents should trigger notifications."""

    assert should_alert(make_incident("high")) is True
    assert should_alert(make_incident("critical")) is True


def test_should_not_alert_for_low_and_medium():
    """Low and medium incidents should not trigger notifications."""

    assert should_alert(make_incident("low")) is False
    assert should_alert(make_incident("medium")) is False


def test_build_notification_uses_incident_data():
    """Notification content should reflect the incident."""

    incident = make_incident(
        severity="high",
        incident_id=101,
    )

    notification = build_notification(incident)

    assert notification.incident_id == 101
    assert notification.severity == "high"
    assert "[HIGH]" in notification.subject
    assert "Incident #101" in notification.subject
    assert "Database unavailable" in notification.subject


def test_dispatch_returns_successful_delivery_result():
    """Successful provider delivery should be recorded."""

    provider = MagicMock(spec=NotificationProvider)
    provider.channel = NotificationChannel.CONSOLE
    provider.send.return_value = True

    results = dispatch_alert_with_results(
        make_incident("critical", 102),
        providers=[provider],
    )

    assert len(results) == 1
    assert results[0].channel == "console"
    assert results[0].incident_id == 102
    assert results[0].success is True
    provider.send.assert_called_once()


def test_dispatch_returns_failed_delivery_result():
    """Failed provider delivery should be recorded."""

    provider = MagicMock(spec=NotificationProvider)
    provider.channel = NotificationChannel.EMAIL
    provider.send.return_value = False

    results = dispatch_alert_with_results(
        make_incident("critical", 103),
        providers=[provider],
    )

    assert len(results) == 1
    assert results[0].channel == "email"
    assert results[0].incident_id == 103
    assert results[0].success is False


def test_dispatch_handles_provider_exception():
    """A provider exception should become a failed delivery result."""

    provider = MagicMock(spec=NotificationProvider)
    provider.channel = NotificationChannel.WEBHOOK
    provider.send.side_effect = RuntimeError("Webhook unavailable")

    results = dispatch_alert_with_results(
        make_incident("critical", 104),
        providers=[provider],
    )

    assert len(results) == 1
    assert results[0].channel == "webhook"
    assert results[0].incident_id == 104
    assert results[0].success is False


def test_dispatch_processes_multiple_providers():
    """Multiple notification providers should be processed independently."""

    console_provider = MagicMock(spec=NotificationProvider)
    console_provider.channel = NotificationChannel.CONSOLE
    console_provider.send.return_value = True

    email_provider = MagicMock(spec=NotificationProvider)
    email_provider.channel = NotificationChannel.EMAIL
    email_provider.send.return_value = False

    webhook_provider = MagicMock(spec=NotificationProvider)
    webhook_provider.channel = NotificationChannel.WEBHOOK
    webhook_provider.send.return_value = True

    results = dispatch_alert_with_results(
        make_incident("critical", 105),
        providers=[
            console_provider,
            email_provider,
            webhook_provider,
        ],
    )

    assert len(results) == 3
    assert results[0].success is True
    assert results[1].success is False
    assert results[2].success is True

    assert dispatch_alert(
        make_incident("critical", 106),
        provider=console_provider,
    ) is True


def test_dispatch_returns_empty_for_non_alert_severity():
    """Non-alert severities should produce no delivery attempts."""

    provider = MagicMock(spec=NotificationProvider)
    provider.channel = NotificationChannel.CONSOLE

    results = dispatch_alert_with_results(
        make_incident("medium", 107),
        providers=[provider],
    )

    assert results == []
    provider.send.assert_not_called()
