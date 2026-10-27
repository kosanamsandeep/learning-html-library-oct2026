"""
Bulkhead Pattern - Isolate failures to prevent cascading across the system.
Inspired by: Ship bulkheads, Netflix Hystrix thread pools, Resilience4j Bulkhead

Like a ship's bulkhead compartments - if one floods, the others stay dry.
Each service gets its own resource pool (semaphore/thread pool).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class BulkheadConfig:
    """Configuration for a bulkhead."""

    name: str = "default"
    max_concurrent: int = 10  # Max simultaneous calls
    max_wait_queue: int = 5  # Max waiting in queue


@dataclass
class BulkheadStats:
    """Represents BulkheadStats in this learning project."""
    total_calls: int = 0
    active_calls: int = 0
    rejected_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    max_active_seen: int = 0


class Bulkhead:
    """
    Bulkhead isolates resource usage per service.
    Limits concurrent access to prevent one slow service from consuming all resources.
    """

    def __init__(self, config: BulkheadConfig | None = None):
        """Initialize the object with the dependencies or starting values it needs."""
        self._config = config or BulkheadConfig()
        self._stats = BulkheadStats()
        self._active: int = 0
        self._waiting: int = 0

    @property
    def stats(self) -> BulkheadStats:
        """Perform the stats step used by this project."""
        return self._stats

    @property
    def name(self) -> str:
        """Perform the name step used by this project."""
        return self._config.name

    @property
    def available_slots(self) -> int:
        """Perform the available slots step used by this project."""
        return self._config.max_concurrent - self._active

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function within bulkhead limits."""
        self._stats.total_calls += 1

        if self._active >= self._config.max_concurrent:
            self._stats.rejected_calls += 1
            raise BulkheadFullError(
                f"Bulkhead '{self._config.name}' is full "
                f"({self._active}/{self._config.max_concurrent} active). "
                f"Request rejected."
            )

        self._active += 1
        self._stats.active_calls = self._active
        self._stats.max_active_seen = max(self._stats.max_active_seen, self._active)

        try:
            result = func(*args, **kwargs)
            self._stats.successful_calls += 1
            return result
        except Exception:
            self._stats.failed_calls += 1
            raise
        finally:
            self._active -= 1
            self._stats.active_calls = self._active

    def release(self) -> None:
        """Manually release a slot (for async scenarios)."""
        if self._active > 0:
            self._active -= 1


class BulkheadFullError(Exception):
    """Raised when bulkhead is at capacity."""

    pass
