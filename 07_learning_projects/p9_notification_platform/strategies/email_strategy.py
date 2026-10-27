"""
=============================================================================
PROJECT 9: NOTIFICATION PLATFORM
=============================================================================
FILE: strategies/email_strategy.py
PURPOSE: Email sending strategy implementation
=============================================================================
"""

import re
from datetime import datetime
from .notification_strategy import (
    NotificationStrategy,
    Notification,
    NotificationResult,
)


class EmailStrategy(NotificationStrategy):
    """
    CONCRETE STRATEGY: Sends notifications via email.

    In production, this would use SMTP, SendGrid, or AWS SES.
    Here we simulate the sending for educational purposes.
    """

    def __init__(
        self, smtp_host: str = "smtp.example.com", smtp_port: int = 587
    ) -> None:
        # Configuration for this strategy
        """Initialize the object with the dependencies or starting values it needs."""
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._sent_count = 0

    def send(self, notification: Notification) -> NotificationResult:
        """
        Send notification via email.

        STRATEGY EXECUTION:
        - Validates recipient format
        - Formats the email (subject, body, headers)
        - "Sends" it (simulated)
        - Returns success/failure result
        """
        if not self.validate_recipient(notification.recipient):
            notification.status = "FAILED"
            notification.error = "Invalid email format"
            return NotificationResult(
                success=False,
                notification_id=notification.notification_id,
                channel="EMAIL",
                message=f"Invalid email: {notification.recipient}",
            )

        # Simulate sending (in production: actual SMTP call)
        notification.status = "SENT"
        notification.sent_at = datetime.now()
        self._sent_count += 1

        return NotificationResult(
            success=True,
            notification_id=notification.notification_id,
            channel="EMAIL",
            message=f"Email sent to {notification.recipient} via {self._smtp_host}",
        )

    def get_channel_name(self) -> str:
        """Return the requested item or information if it exists."""
        return "EMAIL"

    def validate_recipient(self, recipient: str) -> bool:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, recipient))
