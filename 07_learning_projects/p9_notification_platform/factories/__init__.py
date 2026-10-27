"""
=============================================================================
FACTORIES PACKAGE - The Object Creation Layer
=============================================================================
Factories centralize object creation logic.
Instead of scattering 'Notification(...)' calls everywhere,
use NotificationFactory to create properly configured notifications.
=============================================================================
"""

from factories.notification_factory import NotificationFactory

__all__ = ["NotificationFactory"]
