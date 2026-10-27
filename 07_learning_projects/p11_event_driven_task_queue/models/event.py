"""
=============================================================================
PROJECT 11: EVENT-DRIVEN TASK QUEUE
=============================================================================
FILE: models/event.py
PURPOSE: Core event and task domain models

PATTERNS: Observer, Publisher/Subscriber, Command Pattern
REAL-WORLD ANALOGY: Celery, RabbitMQ, AWS SQS, Redis Queue

EVENT-DRIVEN ARCHITECTURE:
- Components communicate by publishing/subscribing to events
- Loose coupling: publisher doesn't know who listens
- Async-ready: tasks can be processed later
- Scalable: add more workers without changing publishers

GOLDEN STANDARD: This mirrors how Celery + RabbitMQ work internally.
=============================================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class EventPriority(Enum):
    """Priority levels for event processing order."""

    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class TaskStatus(Enum):
    """Lifecycle states of a task in the queue."""

    PENDING = "PENDING"  # Waiting in queue
    PROCESSING = "PROCESSING"  # Worker picked it up
    COMPLETED = "COMPLETED"  # Finished successfully
    FAILED = "FAILED"  # Failed with error
    RETRYING = "RETRYING"  # Will retry after backoff
    DEAD = "DEAD"  # Max retries exhausted


@dataclass
class Event:
    """
    An EVENT is something that happened in the system.

    Events are IMMUTABLE facts:
    - "UserRegistered" happened at time T
    - "OrderPlaced" happened at time T
    - "PaymentReceived" happened at time T

    Events CANNOT be undone — they are history.
    """

    event_id: str = field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:8]}")
    event_type: str = ""  # e.g. "user.registered", "order.placed"
    payload: dict = field(default_factory=dict)  # Event data
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = ""  # Which service/module emitted this
    priority: EventPriority = EventPriority.NORMAL
    metadata: dict = field(default_factory=dict)


@dataclass
class Task:
    """
    A TASK is a unit of work to be executed asynchronously.

    DIFFERENCE: Event vs Task
    - Event = "something happened" (notification, fact)
    - Task = "do this work" (command, action)

    Tasks have lifecycle: PENDING → PROCESSING → COMPLETED/FAILED
    Tasks can be retried. Events cannot.
    """

    task_id: str = field(default_factory=lambda: f"TSK-{uuid.uuid4().hex[:8]}")
    task_type: str = ""  # e.g. "send_email", "process_payment"
    payload: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: EventPriority = EventPriority.NORMAL
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str | None = None
    completed_at: str | None = None
    result: Any = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict = field(default_factory=dict)

    def can_retry(self) -> bool:
        """Check if the task has retries remaining."""
        return self.retry_count < self.max_retries

    def mark_processing(self) -> None:
        """Perform the mark processing step used by this project."""
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.now().isoformat()

    def mark_completed(self, result: Any = None) -> None:
        """Perform the mark completed step used by this project."""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now().isoformat()

    def mark_failed(self, error: str) -> None:
        """Perform the mark failed step used by this project."""
        if self.can_retry():
            self.status = TaskStatus.RETRYING
            self.retry_count += 1
        else:
            self.status = TaskStatus.DEAD
        self.error = error

    def mark_dead(self, error: str) -> None:
        """Perform the mark dead step used by this project."""
        self.status = TaskStatus.DEAD
        self.error = error
        self.completed_at = datetime.now().isoformat()
