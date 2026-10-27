"""
Choreographed Saga
==================
No central coordinator. Each service publishes events and reacts to the
events of other services. When a step fails, its `<step>_FAILED` event is
published, and the services that already ran react by compensating.

Inspired by: NServiceBus Sagas, event-driven microservice choreography
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List


@dataclass
class SagaEvent:
    """An immutable event travelling between participants of a saga."""

    event_type: str
    saga_id: str
    payload: Dict[str, object] = field(default_factory=dict)
    source: str = ""


class EventBus:
    """In-process publish/subscribe bus (events delivered in publish order)."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[SagaEvent], None]]] = defaultdict(list)
        self.delivered: List[SagaEvent] = []

    def subscribe(self, event_type: str, handler: Callable[[SagaEvent], None]) -> None:
        """Register a handler that reacts to `event_type`."""
        self._subscribers[event_type].append(handler)

    def publish(self, event: SagaEvent) -> None:
        """Deliver an event to every subscriber, in registration order."""
        self.delivered.append(event)
        for handler in list(self._subscribers.get(event.event_type, ())):
            handler(event)


class Service:
    """A single microservice that reacts to events and emits new ones.

    Forward handling: when `trigger` arrives, run `action`. On success
    publish `success_event`; on failure publish `<success_event>_FAILED`,
    which other services treat as the cue to compensate.
    """

    def __init__(self, name: str, bus: EventBus) -> None:
        self.name = name
        self.bus = bus
        self.compensated: List[str] = []
        self.failures: Dict[str, str] = {}

    def subscribe_forward(
        self,
        trigger: str,
        success_event: str,
        action: Callable[[SagaEvent], None],
    ) -> None:
        """React to `trigger` by running `action`, then emit an outcome event."""

        def handler(event: SagaEvent) -> None:
            try:
                action(event)
                self.bus.publish(SagaEvent(success_event, event.saga_id, event.payload, self.name))
            except Exception as exc:  # noqa: BLE001 - a step failure must not crash the bus
                self.failures[trigger] = str(exc)
                self.bus.publish(
                    SagaEvent(f"{success_event}_FAILED", event.saga_id, event.payload, self.name)
                )

        self.bus.subscribe(trigger, handler)

    def subscribe_compensate(
        self,
        trigger: str,
        success_event: str,
        compensation: Callable[[SagaEvent], None],
    ) -> None:
        """React to a `<step>_FAILED` event by rolling the step back."""

        def handler(event: SagaEvent) -> None:
            compensation(event)
            self.compensated.append(trigger)
            self.bus.publish(SagaEvent(success_event, event.saga_id, event.payload, self.name))

        self.bus.subscribe(trigger, handler)
