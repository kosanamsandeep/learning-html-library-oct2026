"""
PROJECT 9: SMS and Push notification strategies.
"""

import re
from datetime import datetime
from .notification_strategy import (
    NotificationStrategy,
    Notification,
    NotificationResult,
)


class SMSStrategy(NotificationStrategy):
    """
    CONCRETE STRATEGY: Sends notifications via SMS.

    Different channel, same interface!
    In production: Twilio, AWS SNS, etc.
    """

    def __init__(self, provider: str = "twilio") -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self._provider = provider
        self._sent_count = 0
        # SMS has character limits
        self.MAX_LENGTH = 160

    def send(self, notification: Notification) -> NotificationResult:
        """Perform the send step used by this project."""
        if not self.validate_recipient(notification.recipient):
            notification.status = "FAILED"
            return NotificationResult(
                success=False,
                notification_id=notification.notification_id,
                channel="SMS",
                message=f"Invalid phone number: {notification.recipient}",
            )

        # SMS-specific: truncate long messages
        body = notification.body
        if len(body) > self.MAX_LENGTH:
            body = body[:157] + "..."

        notification.status = "SENT"
        notification.sent_at = datetime.now()
        self._sent_count += 1

        return NotificationResult(
            success=True,
            notification_id=notification.notification_id,
            channel="SMS",
            message=f"SMS sent to {notification.recipient} ({len(body)} chars)",
        )

    def get_channel_name(self) -> str:
        """Return the requested item or information if it exists."""
        return "SMS"

    def validate_recipient(self, recipient: str) -> bool:
        """Validate phone number format (simple check)."""
        return bool(re.match(r"^\+?[\d\-\s]{7,15}$", recipient))


class PushStrategy(NotificationStrategy):
    """
    CONCRETE STRATEGY: Sends push notifications.

    In production: Firebase Cloud Messaging (FCM), Apple Push (APNs).
    """

    def __init__(self, platform: str = "fcm") -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self._platform = platform
        self._sent_count = 0

    def send(self, notification: Notification) -> NotificationResult:
        """Perform the send step used by this project."""
        if not self.validate_recipient(notification.recipient):
            notification.status = "FAILED"
            return NotificationResult(
                success=False,
                notification_id=notification.notification_id,
                channel="PUSH",
                message=f"Invalid device token: {notification.recipient}",
            )

        notification.status = "SENT"
        notification.sent_at = datetime.now()
        self._sent_count += 1

        return NotificationResult(
            success=True,
            notification_id=notification.notification_id,
            channel="PUSH",
            message=f"Push sent to device {notification.recipient[:12]}... via {self._platform}",
        )

    def get_channel_name(self) -> str:
        """Return the requested item or information if it exists."""
        return "PUSH"

    def validate_recipient(self, recipient: str) -> bool:
        """Device tokens are typically 64+ character hex strings."""
        return len(recipient) >= 16 and recipient.isalnum()


class SlackStrategy(NotificationStrategy):
    """CONCRETE STRATEGY: Sends notifications to Slack channels."""

    def __init__(self, workspace: str = "default") -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self._workspace = workspace
        self._sent_count = 0

    def send(self, notification: Notification) -> NotificationResult:
        """Perform the send step used by this project."""
        if not self.validate_recipient(notification.recipient):
            notification.status = "FAILED"
            return NotificationResult(
                success=False,
                notification_id=notification.notification_id,
                channel="SLACK",
                message=f"Invalid Slack channel: {notification.recipient}",
            )

        notification.status = "SENT"
        notification.sent_at = datetime.now()
        self._sent_count += 1

        return NotificationResult(
            success=True,
            notification_id=notification.notification_id,
            channel="SLACK",
            message=f"Slack message sent to {notification.recipient}",
        )

    def get_channel_name(self) -> str:
        """Return the requested item or information if it exists."""
        return "SLACK"

    def validate_recipient(self, recipient: str) -> bool:
        """Slack channel starts with # or is a user ID."""
        return recipient.startswith("#") or recipient.startswith("@")
