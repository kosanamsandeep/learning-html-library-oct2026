"""
Idempotency Keys
================
A client sends a key with each logical operation. If a retry arrives with
the same key, the store returns the original result instead of re-running
the operation. This makes exactly-once behavior achievable over networks
that can drop or duplicate messages.

Inspired by: Stripe idempotency keys, AWS Lambda IdempotencyConfig
"""

from typing import Callable, Dict, Tuple


class IdempotencyStore:
    """Maps idempotency keys to their completed result."""

    def __init__(self) -> None:
        self._responses: Dict[str, object] = {}

    def execute(self, key: str, operation: Callable[[], object]) -> Tuple[object, bool]:
        """Run `operation` once per key. Returns (result, was_replayed)."""
        if key in self._responses:
            return self._responses[key], True
        result = operation()
        self._responses[key] = result
        return result, False
