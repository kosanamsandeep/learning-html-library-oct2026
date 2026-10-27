"""
=============================================================================
PROJECT 9: NOTIFICATION PLATFORM
=============================================================================
FILE: factories/notification_factory.py
PURPOSE: FACTORY PATTERN - Creates the right notification object

FACTORY PATTERN EXPLAINED:
- Factory = Object Creation Expert
- Instead of scattering "new Notification(...)" everywhere,
  centralize creation in a factory
- Factory decides WHAT to create based on input parameters
- Client code doesn't need to know creation details

FACTORY vs STRATEGY:
- Factory CREATES objects (decides WHAT)
- Strategy EXECUTES behavior (decides HOW)
- They work together: Factory creates → Strategy executes
=============================================================================
"""

import uuid
from strategies.notification_strategy import Notification


class NotificationFactory:
    """
    FACTORY: Creates properly configured Notification objects.

    WHY A FACTORY?
    - Centralized validation and defaults
    - Consistent ID generation
    - Priority rules applied consistently
    - Different notification types have different requirements

    WITHOUT FACTORY:
        # Scattered creation, inconsistent, error-prone
        n1 = Notification(id=???, recipient="...", ...)
        n2 = Notification(id=???, recipient="...", ...)

    WITH FACTORY:
        # Consistent, validated, properly configured
        n1 = factory.create_email("to@x.com", "Subject", "Body")
        n2 = factory.create_sms("+1234567890", "Message")
    """

    @staticmethod
    def _generate_id() -> str:
        """Perform the generate id step used by this project."""
        return f"NTF-{uuid.uuid4().hex[:8].upper()}"

    @classmethod
    def create_email(
        cls, recipient: str, subject: str, body: str, priority: str = "NORMAL"
    ) -> Notification:
        """Factory method for email notifications."""
        return Notification(
            notification_id=cls._generate_id(),
            recipient=recipient,
            subject=subject,
            body=body,
            channel="EMAIL",
            priority=priority,
        )

    @classmethod
    def create_sms(
        cls, phone_number: str, message: str, priority: str = "NORMAL"
    ) -> Notification:
        """Factory method for SMS notifications."""
        return Notification(
            notification_id=cls._generate_id(),
            recipient=phone_number,
            subject="",  # SMS has no subject
            body=message,
            channel="SMS",
            priority=priority,
        )

    @classmethod
    def create_push(
        cls,
        device_token: str,
        title: str,
        body: str,
        priority: str = "NORMAL",
        metadata: dict | None = None,
    ) -> Notification:
        """Factory method for push notifications."""
        return Notification(
            notification_id=cls._generate_id(),
            recipient=device_token,
            subject=title,
            body=body,
            channel="PUSH",
            priority=priority,
            metadata=metadata or {},
        )

    @classmethod
    def create_slack(
        cls, channel: str, message: str, priority: str = "NORMAL"
    ) -> Notification:
        """Factory method for Slack notifications."""
        return Notification(
            notification_id=cls._generate_id(),
            recipient=channel,
            subject="",
            body=message,
            channel="SLACK",
            priority=priority,
        )

    @classmethod
    def create_from_template(
        cls,
        channel: str,
        recipient: str,
        template_name: str,
        template_vars: dict,
        priority: str = "NORMAL",
    ) -> Notification:
        """
        TEMPLATE FACTORY METHOD:
        Create notification from a predefined template.

        Useful for: welcome emails, password resets, alerts, etc.
        """
        templates = {
            "welcome": {
                "subject": "Welcome to {app_name}!",
                "body": "Hi {user_name}, welcome aboard! Start by exploring {feature}.",
            },
            "password_reset": {
                "subject": "Password Reset Request",
                "body": "Hi {user_name}, use code {reset_code} to reset your password.",
            },
            "alert": {
                "subject": "⚠️ Alert: {alert_type}",
                "body": "{alert_message}",
            },
        }

        template = templates.get(
            template_name, {"subject": "Notification", "body": "{message}"}
        )
        subject = template["subject"].format(**template_vars)
        body = template["body"].format(**template_vars)

        return Notification(
            notification_id=cls._generate_id(),
            recipient=recipient,
            subject=subject,
            body=body,
            channel=channel.upper(),
            priority=priority,
            metadata={"template": template_name},
        )
