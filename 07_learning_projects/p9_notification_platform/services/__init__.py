"""
=============================================================================
SERVICES PACKAGE - The Orchestration Layer
=============================================================================
Services coordinate between factories and strategies.
They don't know HOW to send (that's Strategy's job) or
HOW to create (that's Factory's job) — they just orchestrate.
=============================================================================
"""

from services.notification_service import NotificationService

__all__ = ["NotificationService"]
