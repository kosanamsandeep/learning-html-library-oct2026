"""
Retry with Exponential Backoff - Automatically retry failed operations.
Inspired by: AWS SDK retry logic, Google Cloud client libraries, Tenacity (Python)

Strategy: Wait longer between each retry attempt.
  Attempt 1: wait 1s
  Attempt 2: wait 2s
  Attempt 3: wait 4s
  Attempt 4: wait 8s
  (with optional jitter to prevent thundering herd)
"""

from __future__ import annotations
import time
import random
from dataclasses import dataclass
from typing import Any, Callable, Type


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    base_delay: float = 1.0  # Initial delay in seconds
    max_delay: float = 30.0  # Cap on delay
    exponential_base: float = 2.0  # Multiplier each retry
    jitter: bool = True  # Add randomness to prevent thundering herd
    retryable_exceptions: tuple = (Exception,)  # Which exceptions to retry on


@dataclass
class RetryResult:
    """Result of a retry operation."""

    success: bool
    result: Any = None
    attempts: int = 0
    total_delay: float = 0.0
    last_exception: Exception | None = None
    delays: list = None


class RetryWithBackoff:
    """
    Retry mechanism with exponential backoff and jitter.

    Backoff formula: delay = min(base_delay * (exponential_base ^ attempt), max_delay)
    With jitter: delay = random(0, calculated_delay)
    """

    def __init__(self, config: RetryConfig | None = None):
        """Initialize the object with the dependencies or starting values it needs."""
        self._config = config or RetryConfig()

    def execute(self, func: Callable, *args, **kwargs) -> RetryResult:
        """Execute function with retry logic."""
        attempts = 0
        total_delay = 0.0
        delays = []
        last_exception = None

        for attempt in range(self._config.max_retries + 1):
            attempts += 1
            try:
                result = func(*args, **kwargs)
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_delay=total_delay,
                    delays=delays,
                )
            except self._config.retryable_exceptions as e:
                last_exception = e
                if attempt < self._config.max_retries:
                    delay = self._calculate_delay(attempt)
                    delays.append(delay)
                    total_delay += delay
                    # In real code: time.sleep(delay)
                    # For demo, we just track the delays

        return RetryResult(
            success=False,
            attempts=attempts,
            total_delay=total_delay,
            last_exception=last_exception,
            delays=delays,
        )

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = self._config.base_delay * (self._config.exponential_base**attempt)
        delay = min(delay, self._config.max_delay)

        if self._config.jitter:
            delay = random.uniform(0, delay)

        return round(delay, 3)

    def execute_with_sleep(self, func: Callable, *args, **kwargs) -> RetryResult:
        """Execute with actual sleep between retries (for real usage)."""
        attempts = 0
        total_delay = 0.0
        delays = []
        last_exception = None

        for attempt in range(self._config.max_retries + 1):
            attempts += 1
            try:
                result = func(*args, **kwargs)
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_delay=total_delay,
                    delays=delays,
                )
            except self._config.retryable_exceptions as e:
                last_exception = e
                if attempt < self._config.max_retries:
                    delay = self._calculate_delay(attempt)
                    delays.append(delay)
                    total_delay += delay
                    time.sleep(delay)

        return RetryResult(
            success=False,
            attempts=attempts,
            total_delay=total_delay,
            last_exception=last_exception,
            delays=delays,
        )
