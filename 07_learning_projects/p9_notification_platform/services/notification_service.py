"""
=============================================================================
PROJECT 9: NOTIFICATION PLATFORM
=============================================================================
FILE: services/notification_service.py
PURPOSE: ORCHESTRATION SERVICE - Combines Factory + Strategy patterns

THIS IS WHERE EVERYTHING COMES TOGETHER:
1. Factory CREATES the notification object
2. Strategy Registry SELECTS the right sending strategy
3. Strategy EXECUTES the send operation
4. Service TRACKS results and provides retry logic

PATTERN SYNERGY:
┌──────────────────────────────────────────────────────────┐
│  Client  →  Service  →  Factory + Strategy Registry      │
│                              │           │                │
│                       Creates Object   Selects How        │
│                              │           │                │
│                              └─────┬─────┘                │
│                                    │                      │
│                              Strategy.send(notification)  │
└──────────────────────────────────────────────────────────┘
=============================================================================
"""

from typing import Optional
from datetime import datetime

from strategies.notification_strategy import (
    NotificationStrategy,
    Notification,
    NotificationResult,
)
from strategies.email_strategy import EmailStrategy
from strategies.channel_strategies import SMSStrategy, PushStrategy, SlackStrategy
from factories.notification_factory import NotificationFactory


class NotificationService:
    """
    SERVICE LAYER: Orchestrates notification sending.

    Responsibilities:
    1. Maintain a registry of channel → strategy mapping
    2. Use Factory to create notifications
    3. Use Strategy to send notifications
    4. Track send history and results
    5. Provide retry logic for failed sends

    KEY DESIGN DECISIONS:
    - Strategies are registered at startup (DI-friendly)
    - New channels can be added WITHOUT modifying this class (Open/Closed)
    - Factory handles object creation, service handles orchestration
    """

    def __init__(self):
        # ------------------------------------------------------------------
        # STRATEGY REGISTRY: Maps channel names to strategy instances.
        # This is the Strategy Pattern's "context" - it decides which
        # strategy to delegate to based on the notification's channel.
        # ------------------------------------------------------------------
        """Initialize the object with the dependencies or starting values it needs."""
        self._strategies: dict[str, NotificationStrategy] = {}

        # ------------------------------------------------------------------
        # HISTORY: Track all sent notifications and their results.
        # Useful for auditing, retries, and analytics.
        # ------------------------------------------------------------------
        self._history: list[dict] = []

        # ------------------------------------------------------------------
        # Register default strategies.
        # In production, these would be injected via DI container.
        # ------------------------------------------------------------------
        self._register_default_strategies()

    def _register_default_strategies(self) -> None:
        """Register the built-in notification strategies."""
        self.register_strategy("EMAIL", EmailStrategy())
        self.register_strategy("SMS", SMSStrategy())
        self.register_strategy("PUSH", PushStrategy())
        self.register_strategy("SLACK", SlackStrategy())

    # ======================================================================
    # STRATEGY REGISTRATION (Open/Closed Principle)
    # ======================================================================

    def register_strategy(self, channel: str, strategy: NotificationStrategy) -> None:
        """
        Register a new sending strategy for a channel.

        WHY THIS MATTERS:
        - Adding WhatsApp? Just create WhatsAppStrategy and register it.
        - NO changes to existing code. ZERO modifications.
        - This is the Open/Closed Principle in action.
        """
        self._strategies[channel.upper()] = strategy

    def get_available_channels(self) -> list[str]:
        """Return list of registered notification channels."""
        return list(self._strategies.keys())

    # ======================================================================
    # SENDING NOTIFICATIONS (Factory creates, Strategy sends)
    # ======================================================================

    def send_email(
        self, recipient: str, subject: str, body: str, priority: str = "NORMAL"
    ) -> NotificationResult:
        """
        Send an email notification.

        FLOW:
        1. Factory creates a properly configured Notification
        2. Service selects EmailStrategy from registry
        3. EmailStrategy.send() handles delivery
        4. Result is logged in history
        """
        notification = NotificationFactory.create_email(
            recipient, subject, body, priority
        )
        return self._send(notification)

    def send_sms(
        self, phone_number: str, message: str, priority: str = "NORMAL"
    ) -> NotificationResult:
        """Send an SMS notification."""
        notification = NotificationFactory.create_sms(phone_number, message, priority)
        return self._send(notification)

    def send_push(
        self, device_token: str, title: str, body: str, priority: str = "NORMAL"
    ) -> NotificationResult:
        """Send a push notification."""
        notification = NotificationFactory.create_push(
            device_token, title, body, priority
        )
        return self._send(notification)

    def send_slack(
        self, channel: str, message: str, priority: str = "NORMAL"
    ) -> NotificationResult:
        """Send a Slack notification."""
        notification = NotificationFactory.create_slack(channel, message, priority)
        return self._send(notification)

    def send_from_template(
        self,
        channel: str,
        recipient: str,
        template_name: str,
        template_vars: dict,
        priority: str = "NORMAL",
    ) -> NotificationResult:
        """Send a notification using a predefined template."""
        notification = NotificationFactory.create_from_template(
            channel, recipient, template_name, template_vars, priority
        )
        return self._send(notification)

    # ======================================================================
    # BROADCAST (Send to multiple channels at once)
    # ======================================================================

    def broadcast(
        self,
        message: str,
        channels: list[str],
        recipients: dict[str, str],
        priority: str = "NORMAL",
    ) -> list[NotificationResult]:
        """
        Broadcast a message across multiple channels.

        EXAMPLE:
            service.broadcast(
                message="Server is down!",
                channels=["EMAIL", "SLACK", "SMS"],
                recipients={
                    "EMAIL": "admin@company.com",
                    "SLACK": "#alerts",
                    "SMS": "+1234567890"
                },
                priority="URGENT"
            )
        """
        results = []
        for channel in channels:
            recipient = recipients.get(channel.upper(), "")
            if not recipient:
                continue

            if channel.upper() == "EMAIL":
                result = self.send_email(
                    recipient, "Broadcast Alert", message, priority
                )
            elif channel.upper() == "SMS":
                result = self.send_sms(recipient, message, priority)
            elif channel.upper() == "PUSH":
                result = self.send_push(recipient, "Alert", message, priority)
            elif channel.upper() == "SLACK":
                result = self.send_slack(recipient, message, priority)
            else:
                continue

            results.append(result)

        return results

    # ======================================================================
    # INTERNAL: Core send logic + history tracking
    # ======================================================================

    def _send(self, notification: Notification) -> NotificationResult:
        """
        Internal send method - the HEART of the service.

        This is where Factory meets Strategy:
        1. Notification was already CREATED by Factory
        2. Now we SELECT the right Strategy from registry
        3. Strategy EXECUTES the send
        4. We RECORD the result
        """
        # Find the right strategy for this channel
        strategy = self._strategies.get(notification.channel.upper())

        if strategy is None:
            # No strategy registered for this channel
            result = NotificationResult(
                notification_id=notification.notification_id,
                success=False,
                channel=notification.channel,
                message=f"No strategy registered for channel: {notification.channel}",
            )
        else:
            # Delegate to the strategy (Strategy Pattern execution)
            result = strategy.send(notification)

        # Record in history for auditing
        self._history.append(
            {
                "notification_id": notification.notification_id,
                "channel": notification.channel,
                "recipient": notification.recipient,
                "success": result.success,
                "timestamp": datetime.now().isoformat(),
                "error": result.message,
            }
        )

        return result

    # ======================================================================
    # RETRY LOGIC
    # ======================================================================

    def retry_failed(self, max_retries: int = 3) -> list[NotificationResult]:
        """
        Retry all failed notifications.

        In production: use exponential backoff, dead-letter queues, etc.
        Here we demonstrate the concept simply.
        """
        failed = [h for h in self._history if not h["success"]]
        results = []

        for entry in failed[:max_retries]:
            # Re-attempt would recreate and resend
            # For demo, we just log the retry attempt
            results.append(
                NotificationResult(
                    notification_id=entry["notification_id"],
                    success=False,
                    channel=entry["channel"],
                    message="Retry not implemented in demo",
                )
            )

        return results

    # ======================================================================
    # ANALYTICS / HISTORY
    # ======================================================================

    def get_history(self) -> list[dict]:
        """Return full send history."""
        return self._history.copy()

    def get_stats(self) -> dict:
        """
        Get send statistics.

        Returns dict with total, success, failure counts per channel.
        """
        stats = {
            "total": len(self._history),
            "success": sum(1 for h in self._history if h["success"]),
            "failed": sum(1 for h in self._history if not h["success"]),
            "by_channel": {},
        }

        for entry in self._history:
            ch = entry["channel"]
            if ch not in stats["by_channel"]:
                stats["by_channel"][ch] = {"total": 0, "success": 0, "failed": 0}
            stats["by_channel"][ch]["total"] += 1
            if entry["success"]:
                stats["by_channel"][ch]["success"] += 1
            else:
                stats["by_channel"][ch]["failed"] += 1

        return stats
