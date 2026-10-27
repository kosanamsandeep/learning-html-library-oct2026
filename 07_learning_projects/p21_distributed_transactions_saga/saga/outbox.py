"""
Transactional Outbox
====================
Business state change and the resulting event are committed in the SAME
local transaction (the outbox row). A background dispatcher then publishes
outbox rows, so no event is lost on a crash and none is published twice.

Inspired by: Debezium Outbox, Microservices.io Outbox pattern
"""

from typing import Callable, List, Optional


class OutboxRecord:
    """A single not-yet-published event, stored alongside the business row."""

    def __init__(self, seq: int, aggregate_id: str, event_type: str, payload: dict) -> None:
        self.seq = seq
        self.aggregate_id = aggregate_id
        self.event_type = event_type
        self.payload = payload
        self.published = False


class OutboxStore:
    """An append-only table of events. Rows appear atomically with state changes."""

    def __init__(self) -> None:
        self.records: List[OutboxRecord] = []
        self._seq = 0

    def atomic_write(
        self,
        state_change: Callable[[], None],
        aggregate_id: str,
        event_type: str,
        payload: dict,
    ) -> OutboxRecord:
        """Apply `state_change` AND append the outbox row in one 'transaction'."""
        state_change()
        record = OutboxRecord(self._seq, aggregate_id, event_type, payload)
        self._seq += 1
        self.records.append(record)
        return record

    def pending(self) -> List[OutboxRecord]:
        """Return unpublished records in commit order."""
        return [r for r in self.records if not r.published]


class OutboxDispatcher:
    """Polls the outbox and delivers events, surviving restarts."""

    def __init__(self, store: OutboxStore) -> None:
        self.store = store
        self.delivered: List[str] = []

    def poll(self, limit: Optional[int] = None) -> int:
        """Publish the oldest unpublished events. `limit` simulates a batch window."""
        batch = self.store.pending()[:limit]
        for record in batch:
            record.published = True
            self.delivered.append(record.event_type)
        return len(batch)
