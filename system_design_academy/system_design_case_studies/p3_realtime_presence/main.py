"""P3 Case Study · Real-time Presence Service.

WhatsApp / Slack / Teams show a green dot next to online users. The trick:
each client sends a heartbeat every few seconds. The server keeps a
(user_id -> last_heartbeat_at) map. Anyone whose heartbeat is newer than
`ttl` seconds is "online". TTL eviction does the offline detection for free.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class PresenceService:
    """Track which users are online based on recent heartbeats."""

    ttl_seconds: float = 30.0
    _last_seen: dict[str, float] = field(default_factory=dict)

    def heartbeat(self, user_id: str, now: float | None = None) -> None:
        """Record that `user_id` is alive right now."""
        self._last_seen[user_id] = now if now is not None else time.time()

    def is_online(self, user_id: str, now: float | None = None) -> bool:
        """Return True when the last heartbeat is within the TTL window."""
        last = self._last_seen.get(user_id)
        if last is None:
            return False
        now = now if now is not None else time.time()
        return (now - last) <= self.ttl_seconds

    def online_users(self, now: float | None = None) -> list[str]:
        """List every user whose last heartbeat is still fresh."""
        now = now if now is not None else time.time()
        return sorted(
            u for u, t in self._last_seen.items() if (now - t) <= self.ttl_seconds
        )

    def evict_expired(self, now: float | None = None) -> int:
        """Drop offline users from memory; returns the number removed."""
        now = now if now is not None else time.time()
        gone = [u for u, t in self._last_seen.items() if (now - t) > self.ttl_seconds]
        for u in gone:
            del self._last_seen[u]
        return len(gone)


def main() -> None:
    """Simulate three users beating with different cadences over 90 fake seconds."""
    svc = PresenceService(ttl_seconds=30)
    t0 = 1_000_000.0  # fake start time

    # alice beats every 10s for 80s (stays online)
    # bob beats once at t=0 and never again (goes offline after 30s)
    # carol joins at t=40 and beats steadily
    for t in range(0, 90, 5):
        now = t0 + t
        if t % 10 == 0:
            svc.heartbeat("alice", now=now)
        if t == 0:
            svc.heartbeat("bob", now=now)
        if t >= 40 and t % 10 == 0:
            svc.heartbeat("carol", now=now)

        online = svc.online_users(now=now)
        print(f"t={t:2d}s  online={online}")

    removed = svc.evict_expired(now=t0 + 90)
    print(f"\nevicted {removed} stale entries; final state={svc._last_seen}")


if __name__ == "__main__":
    main()
