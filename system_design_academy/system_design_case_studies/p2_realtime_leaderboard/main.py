"""P2 Case Study · Real-time Leaderboard.

Game leaderboards need three operations to be fast:
  - Update a score for a user.
  - Get the top N players.
  - Get the rank of a specific player.

Redis solves this with ZSET (sorted set) backed by a skip list. Here we
implement the same idea using Python's `SortedList` substitute (we use
`bisect` on a list of (score, user) tuples for clarity).
"""

from __future__ import annotations

from bisect import insort
from dataclasses import dataclass, field


@dataclass
class Leaderboard:
    """Sorted by (-score, user) so the highest scores come first."""

    _scores: dict[str, int] = field(default_factory=dict)
    _ordered: list[tuple[int, str]] = field(default_factory=list)

    def submit(self, user: str, score: int) -> None:
        """Set the score for `user`, replacing any existing entry."""
        if user in self._scores:
            old = self._scores[user]
            self._ordered.remove((-old, user))
        self._scores[user] = score
        insort(self._ordered, (-score, user))

    def top(self, n: int) -> list[tuple[str, int]]:
        """Return the top `n` entries as (user, score) pairs."""
        return [(user, -neg) for neg, user in self._ordered[:n]]

    def rank_of(self, user: str) -> int | None:
        """Return the 1-based rank of `user`, or None when missing."""
        if user not in self._scores:
            return None
        score = self._scores[user]
        # Index in the ordered list = rank - 1.
        return self._ordered.index((-score, user)) + 1

    def around(self, user: str, window: int = 2) -> list[tuple[str, int]]:
        """Return entries around `user` for a 'players near you' view."""
        rank = self.rank_of(user)
        if rank is None:
            return []
        lo = max(0, rank - 1 - window)
        hi = rank - 1 + window + 1
        return [(u, -n) for n, u in self._ordered[lo:hi]]


def main() -> None:
    """Submit scores for a few players and print top / rank / around views."""
    lb = Leaderboard()
    for user, score in [
        ("alice", 1500),
        ("bob", 1800),
        ("carol", 2400),
        ("dan", 2100),
        ("eve", 1750),
        ("frank", 2200),
        ("grace", 1900),
    ]:
        lb.submit(user, score)

    # bob improves and overtakes a couple of players.
    lb.submit("bob", 2350)

    print("--- top 5 ---")
    for u, s in lb.top(5):
        print(f"  {u:>6s} : {s}")

    print(f"\nrank of dan  : {lb.rank_of('dan')}")
    print(f"rank of bob  : {lb.rank_of('bob')}")

    print("\nleaderboard around 'dan' (+/- 2):")
    for u, s in lb.around("dan", window=2):
        print(f"  {u:>6s} : {s}")


if __name__ == "__main__":
    main()
