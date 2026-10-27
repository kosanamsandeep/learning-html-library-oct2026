"""
=============================================================================
PROJECT 11: EVENT-DRIVEN TASK QUEUE
=============================================================================
FILE: bus/event_bus.py
PURPOSE: The Event Bus — central nervous system of event-driven architecture

OBSERVER PATTERN + PUB/SUB:
- Publishers emit events to the bus
- Subscribers register handlers for specific event types
- Bus routes events to the right handlers
- Publishers and subscribers don't know each other

GOLDEN STANDARD REFERENCE:
- Python: blinker, PyPubSub, Django signals
- Enterprise: Apache Kafka, RabbitMQ, AWS EventBridge
- Node.js: EventEmitter

This implementation mirrors Django's signal dispatcher pattern.
=============================================================================
"""

from typing import Callable
from models.event import Event

# Type alias for event handler functions
EventHandler = Callable[[Event], None]


class EventBus:
    """
    Central event dispatcher (Observer/Pub-Sub pattern).

    HOW IT WORKS:
    1. Subscribers call bus.subscribe("order.placed", handler_func)
    2. Publishers call bus.publish(event)
    3. Bus looks up all handlers for that event_type
    4. Bus calls each handler with the event

    ANALOGY:
    Think of a radio station:
    - Publisher = DJ broadcasting on channel "order.placed"
    - Subscriber = Listener tuned to "order.placed"
    - EventBus = The radio infrastructure connecting them

    REAL WORLD:
    - Django Signals: post_save.connect(handler, sender=Model)
    - Node EventEmitter: emitter.on('event', handler)
    - Kafka: consumer.subscribe(topic)
    """

    def __init__(self):
        # Map: event_type → list of handler functions
        """Initialize the object with the dependencies or starting values it needs."""
        self._subscribers: dict[str, list[EventHandler]] = {}
        # History of published events (for debugging/replay)
        self._event_log: list[Event] = []
        # Dead letter queue: events that no one handled
        self._dead_letters: list[Event] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Register a handler for a specific event type.

        MULTIPLE HANDLERS PER EVENT:
        You can subscribe many handlers to the same event type.
        All will be called when that event fires.

        Example:
            bus.subscribe("user.registered", send_welcome_email)
            bus.subscribe("user.registered", create_default_settings)
            bus.subscribe("user.registered", notify_admin)
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """Remove a handler from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                return True
            except ValueError:
                return False
        return False

    def publish(self, event: Event) -> int:
        """
        Publish an event to all registered handlers.

        Returns the number of handlers that processed the event.
        If no handlers exist, event goes to dead letter queue.
        """
        self._event_log.append(event)

        handlers = self._subscribers.get(event.event_type, [])

        if not handlers:
            # No one is listening — dead letter
            self._dead_letters.append(event)
            return 0

        handled_count = 0
        for handler in handlers:
            try:
                handler(event)
                handled_count += 1
            except Exception as e:
                # Log error but don't stop other handlers
                print(f"    [EventBus] Handler error for {event.event_type}: {e}")

        return handled_count

    def publish_many(self, events: list[Event]) -> int:
        """Publish multiple events. Returns total handlers invoked."""
        return sum(self.publish(event) for event in events)

    def get_subscribers(self, event_type: str) -> list[EventHandler]:
        """Return all handlers for an event type."""
        return self._subscribers.get(event_type, []).copy()

    def get_all_event_types(self) -> list[str]:
        """Return all event types that have subscribers."""
        return list(self._subscribers.keys())

    def get_event_log(self) -> list[Event]:
        """Return full event history."""
        return self._event_log.copy()

    def get_dead_letters(self) -> list[Event]:
        """Return events that had no handlers."""
        return self._dead_letters.copy()

    def clear(self) -> None:
        """Reset the bus (useful for testing)."""
        self._subscribers.clear()
        self._event_log.clear()
        self._dead_letters.clear()
