"""PROJECT 9 - strategies package"""

from .notification_strategy import (
    NotificationStrategy,
    Notification,
    NotificationResult,
)
from .email_strategy import EmailStrategy
from .channel_strategies import SMSStrategy, PushStrategy, SlackStrategy

__all__ = [
    "NotificationStrategy",
    "Notification",
    "NotificationResult",
    "EmailStrategy",
    "SMSStrategy",
    "PushStrategy",
    "SlackStrategy",
]
