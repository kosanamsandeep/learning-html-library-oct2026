"""P1 Fundamentals · Rate Limiter.

Three classic algorithms used by API gateways and Stripe-style APIs:
  - Token bucket: smooth refill, allows short bursts up to bucket size.
  - Sliding window log: exact count of requests in the last N seconds.
  - Fixed window counter: cheap, but allows bursts near window boundaries.

This file runs all three side by side so you can see how they behave under
the same request pattern.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class TokenBucket:
    """Refill `rate` tokens per second up to `capacity`; each request costs 1."""

    capacity: int
    rate: float
    tokens: float = field(init=False)
    last: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None:
        """Start the bucket full so the first burst is allowed."""
        self.tokens = float(self.capacity)

    def allow(self) -> bool:
        """Return True when one token is available; refill based on elapsed time."""
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


@dataclass
class SlidingWindowLog:
    """Keep timestamps of recent requests; allow only `limit` per `window` seconds."""

    limit: int
    window: float
    events: deque[float] = field(default_factory=deque)

    def allow(self) -> bool:
        """Drop old timestamps then admit the request when below the limit."""
        now = time.monotonic()
        while self.events and self.events[0] <= now - self.window:
            self.events.popleft()
        if len(self.events) < self.limit:
            self.events.append(now)
            return True
        return False


@dataclass
class FixedWindowCounter:
    """Bucket requests into fixed time windows; cheapest, but boundary-bursty."""

    limit: int
    window: float
    count: int = 0
    window_start: float = field(default_factory=time.monotonic)

    def allow(self) -> bool:
        """Reset the counter when the window rolls over, then admit if under the limit."""
        now = time.monotonic()
        if now - self.window_start >= self.window:
            self.window_start = now
            self.count = 0
        if self.count < self.limit:
            self.count += 1
            return True
        return False


def simulate(name: str, limiter, request_pattern: list[float]) -> None:
    """Run a sequence of relative request times against the limiter and print results."""
    print(f"\n--- {name} ---")
    start = time.monotonic()
    allowed = denied = 0
    for offset in request_pattern:
        while time.monotonic() - start < offset:
            time.sleep(0.001)
        ok = limiter.allow()
        allowed += ok
        denied += not ok
        print(f"  t={offset:4.2f}s -> {'ALLOW' if ok else 'DENY '}")
    print(f"  summary: {allowed} allowed, {denied} denied")


def main() -> None:
    """Show how each algorithm reacts to the same burst + steady pattern."""
    # 5 requests burst, then steady 1 per 0.2s for 1 second
    pattern = [0.0, 0.02, 0.04, 0.06, 0.08] + [0.2 * i for i in range(1, 6)]

    simulate(
        "Token bucket (cap=3, refill=5/s)", TokenBucket(capacity=3, rate=5), pattern
    )
    simulate(
        "Sliding window log (limit=4 / 0.5s)",
        SlidingWindowLog(limit=4, window=0.5),
        pattern,
    )
    simulate(
        "Fixed window counter (limit=4 / 0.5s)",
        FixedWindowCounter(limit=4, window=0.5),
        pattern,
    )


if __name__ == "__main__":
    main()
