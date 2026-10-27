"""
Event Store - Append-only log of domain events.
Inspired by: EventStoreDB, Apache Kafka, Greg Young's Event Sourcing

The Event Store is the single source of truth. Instead of storing current state,
we store the sequence of events that led to the current state. State is always
derivable by replaying events.

Key principles:
  - Events are IMMUTABLE (never modified or deleted)
  - Events are ORDERED (sequence matters)
  - State = fold(initial_state, events)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for all domain events. Immutable (frozen=True).

    An event represents something that HAPPENED in the past.
    Named in past tense: AccountOpened, MoneyDeposited, TransferCompleted.
    """

    event_id: str = field(default_factory=lambda: str(uuid4())[:8])
    event_type: str = ""
    aggregate_id: str = ""  # Which entity this event belongs to
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 0  # Sequence number within aggregate
    data: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


# ─── Concrete Banking Events ─────────────────────────────────────


@dataclass(frozen=True)
class AccountOpened(DomainEvent):
    """Represents AccountOpened in this learning project."""
    event_type: str = "AccountOpened"


@dataclass(frozen=True)
class MoneyDeposited(DomainEvent):
    """Represents MoneyDeposited in this learning project."""
    event_type: str = "MoneyDeposited"


@dataclass(frozen=True)
class MoneyWithdrawn(DomainEvent):
    """Represents MoneyWithdrawn in this learning project."""
    event_type: str = "MoneyWithdrawn"


@dataclass(frozen=True)
class TransferInitiated(DomainEvent):
    """Represents TransferInitiated in this learning project."""
    event_type: str = "TransferInitiated"


@dataclass(frozen=True)
class TransferCompleted(DomainEvent):
    """Represents TransferCompleted in this learning project."""
    event_type: str = "TransferCompleted"


@dataclass(frozen=True)
class TransferFailed(DomainEvent):
    """Represents TransferFailed in this learning project."""
    event_type: str = "TransferFailed"


@dataclass(frozen=True)
class AccountFrozen(DomainEvent):
    """Represents AccountFrozen in this learning project."""
    event_type: str = "AccountFrozen"


@dataclass(frozen=True)
class AccountClosed(DomainEvent):
    """Represents AccountClosed in this learning project."""
    event_type: str = "AccountClosed"


class EventStore:
    """
    Append-only event store. The single source of truth.

    In production, this would be backed by:
      - EventStoreDB
      - Apache Kafka
      - PostgreSQL with append-only table
      - DynamoDB with stream
    """

    def __init__(self):
        # Global ordered log (all events across all aggregates)
        """Initialize the object with the dependencies or starting values it needs."""
        self._global_log: list[DomainEvent] = []
        # Per-aggregate streams (for efficient aggregate loading)
        self._streams: dict[str, list[DomainEvent]] = {}
        # Subscribers for new events (for projections)
        self._subscribers: list[Any] = []

    def append(self, event: DomainEvent) -> None:
        """Append an event to the store (immutable, append-only)."""
        self._global_log.append(event)

        if event.aggregate_id not in self._streams:
            self._streams[event.aggregate_id] = []
        self._streams[event.aggregate_id].append(event)

        # Notify subscribers (projections)
        for subscriber in self._subscribers:
            subscriber.handle_event(event)

    def get_stream(self, aggregate_id: str) -> list[DomainEvent]:
        """Get all events for a specific aggregate (entity)."""
        return self._streams.get(aggregate_id, [])

    def get_all_events(self) -> list[DomainEvent]:
        """Get the global event log (ordered)."""
        return self._global_log.copy()

    def subscribe(self, subscriber) -> None:
        """Subscribe to new events (for projections to stay updated)."""
        self._subscribers.append(subscriber)

    def replay_to(self, subscriber, aggregate_id: str | None = None) -> None:
        """Replay historical events to a subscriber (rebuild projection)."""
        events = self.get_stream(aggregate_id) if aggregate_id else self._global_log
        for event in events:
            subscriber.handle_event(event)

    @property
    def event_count(self) -> int:
        """Perform the event count step used by this project."""
        return len(self._global_log)

    @property
    def stream_count(self) -> int:
        """Perform the stream count step used by this project."""
        return len(self._streams)
