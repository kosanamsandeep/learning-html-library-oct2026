"""P4 Fundamentals · Idempotent API.

Network calls fail and clients retry. Without idempotency, a payment can be
charged twice for the same intent. The standard Stripe-style fix is the
"Idempotency-Key" header: the server remembers the result of the first call
keyed by that header and replays it on every retry.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class IdempotencyStore:
    """Tiny in-memory store of (key -> response) with TTL eviction."""

    ttl_seconds: float = 24 * 3600
    _entries: dict[str, tuple[float, Any]] = field(default_factory=dict)

    def _evict_expired(self) -> None:
        """Drop entries whose TTL has passed (lazy cleanup)."""
        now = time.time()
        for key in [
            k for k, (ts, _) in self._entries.items() if now - ts > self.ttl_seconds
        ]:
            del self._entries[key]

    def get(self, key: str) -> Any | None:
        """Return the stored response for `key`, or None when not yet seen."""
        self._evict_expired()
        entry = self._entries.get(key)
        return entry[1] if entry else None

    def put(self, key: str, response: Any) -> None:
        """Remember the response so future retries with the same key replay it."""
        self._entries[key] = (time.time(), response)


@dataclass
class PaymentAPI:
    """Toy payment endpoint that is safe to retry when the client supplies a key."""

    store: IdempotencyStore = field(default_factory=IdempotencyStore)
    _charges: list[dict[str, Any]] = field(default_factory=list)

    def charge(
        self, idempotency_key: str, amount_cents: int, customer: str
    ) -> dict[str, Any]:
        """Charge once per idempotency_key; replay the first result on retry."""
        cached = self.store.get(idempotency_key)
        if cached is not None:
            return {**cached, "replayed": True}

        # First time: do the work and remember it.
        response = {
            "id": f"ch_{uuid.uuid4().hex[:10]}",
            "amount_cents": amount_cents,
            "customer": customer,
            "status": "succeeded",
            "replayed": False,
        }
        self._charges.append(response)
        self.store.put(idempotency_key, response)
        return response


def simulate_flaky_client(
    api: PaymentAPI, attempt_outcomes: list[Callable[[], None]]
) -> dict[str, Any]:
    """Run a client that retries with the same idempotency key after failures."""
    key = f"order-42-{uuid.uuid4().hex[:6]}"
    last_response: dict[str, Any] | None = None
    for attempt, fail_step in enumerate(attempt_outcomes, start=1):
        print(f"  attempt #{attempt} with key={key}")
        last_response = api.charge(key, amount_cents=9900, customer="cust_001")
        fail_step()  # simulate network glitch after the call
    assert last_response is not None
    return last_response


def main() -> None:
    """Show that 3 retries of the same logical request produce exactly 1 charge."""
    api = PaymentAPI()

    def succeed() -> None:
        """Mark the attempt as completed cleanly."""

    def network_glitch() -> None:
        """Simulate the response being lost after the server processed it."""
        print("     (response dropped; client will retry)")

    result = simulate_flaky_client(api, [network_glitch, network_glitch, succeed])

    print(f"\nfinal response: {result}")
    print(f"total real charges recorded on server: {len(api._charges)}")
    assert len(api._charges) == 1, "idempotency broken: more than one charge created"


if __name__ == "__main__":
    main()
