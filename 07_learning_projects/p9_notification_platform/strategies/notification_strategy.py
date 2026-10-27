"""
=============================================================================
PROJECT 9: NOTIFICATION PLATFORM
=============================================================================
FILE: strategies/notification_strategy.py
PURPOSE: Define notification STRATEGIES (the "how to send" part)

WHAT YOU LEARN HERE:
- STRATEGY PATTERN: Encapsulate algorithms into interchangeable classes
- Each strategy knows HOW to send via one channel (email, SMS, push)
- The context (NotificationService) picks which strategy to use at runtime

ANALOGY: "Factory Creates, Strategy Executes"
- Factory decides WHICH notification to create
- Strategy decides HOW to deliver it
=============================================================================
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Notification:
    """Represents a notification to be sent."""

    notification_id: str
    recipient: str  # Email, phone number, or device ID
    subject: str
    body: str
    channel: str  # EMAIL, SMS, PUSH, SLACK
    priority: str = "NORMAL"  # LOW, NORMAL, HIGH, CRITICAL
    metadata: dict = field(default_factory=dict)
    status: str = "PENDING"  # PENDING, SENT, FAILED
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: datetime | None = None
    error: str = ""


@dataclass
class NotificationResult:
    """Result of sending a notification."""

    success: bool
    notification_id: str
    channel: str
    message: str = ""


class NotificationStrategy(ABC):
    """
    STRATEGY INTERFACE: Defines HOW to send a notification.

    STRATEGY PATTERN EXPLAINED:
    - Each concrete strategy encapsulates ONE sending algorithm
    - EmailStrategy knows how to send emails
    - SMSStrategy knows how to send SMS
    - PushStrategy knows how to send push notifications

    The sending code (service) doesn't know WHICH strategy it's using.
    It just calls strategy.send(notification).

    WHY NOT if/elif/else?
    - Adding new channel = modify existing code (violates Open/Closed)
    - Each strategy can be tested independently
    - Strategies can be swapped at RUNTIME
    """

    @abstractmethod
    def send(self, notification: Notification) -> NotificationResult:
        """Send the notification using this strategy's channel."""
        pass

    @abstractmethod
    def get_channel_name(self) -> str:
        """Return the channel name this strategy handles."""
        pass

    @abstractmethod
    def validate_recipient(self, recipient: str) -> bool:
        """Check if the recipient format is valid for this channel."""
        pass
