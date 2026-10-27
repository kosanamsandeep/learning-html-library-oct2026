"""
Circuit Breaker Pattern - Prevent cascading failures in distributed systems.
Inspired by: Netflix Hystrix, resilience4j, Polly (.NET), Michael Nygard's "Release It!"

The circuit breaker has 3 states:
  CLOSED: Normal operation, requests pass through
  OPEN: Failures exceeded threshold, requests fail fast (no call to service)
  HALF_OPEN: After timeout, allow ONE test request to check if service recovered

Like an electrical circuit breaker - trips to prevent damage from overload.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class CircuitState(Enum):
    """Represents CircuitState in this learning project."""
    CLOSED = "CLOSED"  # Normal - requests flow through
    OPEN = "OPEN"  # Tripped - fail fast
    HALF_OPEN = "HALF_OPEN"  # Testing - one request allowed


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker instance."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes in half-open before closing
    timeout_seconds: float = 30.0  # Time before half-open after opening
    name: str = "default"


@dataclass
class CircuitStats:
    """Statistics for monitoring."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0  # Calls rejected while OPEN
    state_changes: int = 0
    last_failure_time: float = 0.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class CircuitBreaker:
    """
    Circuit Breaker implementation.

    State machine:
      CLOSED --[failure_threshold reached]--> OPEN
      OPEN --[timeout expires]--> HALF_OPEN
      HALF_OPEN --[success_threshold reached]--> CLOSED
      HALF_OPEN --[any failure]--> OPEN
    """

    def __init__(self, config: CircuitBreakerConfig | None = None):
        """Initialize the object with the dependencies or starting values it needs."""
        self._config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._opened_at: float = 0.0
        self._listeners: list[Callable[[CircuitState, CircuitState], None]] = []

    @property
    def state(self) -> CircuitState:
        # Check if we should transition from OPEN to HALF_OPEN
        """Perform the state step used by this project."""
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._opened_at
            if elapsed >= self._config.timeout_seconds:
                self._transition_to(CircuitState.HALF_OPEN)
        return self._state

    @property
    def stats(self) -> CircuitStats:
        """Perform the stats step used by this project."""
        return self._stats

    @property
    def name(self) -> str:
        """Perform the name step used by this project."""
        return self._config.name

    def on_state_change(
        self, listener: Callable[[CircuitState, CircuitState], None]
    ) -> None:
        """Register listener for state changes."""
        self._listeners.append(listener)

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through the circuit breaker.
        Raises CircuitOpenError if circuit is OPEN.
        """
        current_state = self.state  # Triggers OPEN -> HALF_OPEN check
        self._stats.total_calls += 1

        if current_state == CircuitState.OPEN:
            self._stats.rejected_calls += 1
            raise CircuitOpenError(
                f"Circuit '{self._config.name}' is OPEN. "
                f"Failing fast. Retry after {self._config.timeout_seconds}s."
            )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Handle successful call."""
        self._stats.successful_calls += 1
        self._stats.consecutive_failures = 0
        self._stats.consecutive_successes += 1

        if self._state == CircuitState.HALF_OPEN:
            if self._stats.consecutive_successes >= self._config.success_threshold:
                self._transition_to(CircuitState.CLOSED)

    def _on_failure(self) -> None:
        """Handle failed call."""
        self._stats.failed_calls += 1
        self._stats.consecutive_successes = 0
        self._stats.consecutive_failures += 1
        self._stats.last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open goes back to OPEN
            self._transition_to(CircuitState.OPEN)
        elif self._state == CircuitState.CLOSED:
            if self._stats.consecutive_failures >= self._config.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        old_state = self._state
        self._state = new_state
        self._stats.state_changes += 1

        if new_state == CircuitState.OPEN:
            self._opened_at = time.time()
        elif new_state == CircuitState.CLOSED:
            self._stats.consecutive_failures = 0
            self._stats.consecutive_successes = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._stats.consecutive_successes = 0

        for listener in self._listeners:
            listener(old_state, new_state)

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        self._transition_to(CircuitState.CLOSED)
        self._stats = CircuitStats()


class CircuitOpenError(Exception):
    """Raised when circuit is open and call is rejected."""

    pass
