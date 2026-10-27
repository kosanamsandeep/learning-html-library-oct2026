"""P1 Case Study · Distributed Counter (YouTube view-count style).

When a video gets 100k views per second, a single SQL row becomes the
bottleneck — every increment locks it. The standard fix is to shard the
counter across N rows (or N Redis keys) and sum them when reading.

This file simulates many concurrent writers hitting a sharded counter and
shows that the total stays correct while contention is much lower.
"""

from __future__ import annotations

import random
import threading
from dataclasses import dataclass, field


@dataclass
class ShardedCounter:
    """N independent counters; writers pick one at random, reads sum all."""

    shard_count: int = 16
    _shards: list[int] = field(init=False)
    _locks: list[threading.Lock] = field(init=False)

    def __post_init__(self) -> None:
        """Allocate per-shard storage and per-shard locks."""
        self._shards = [0] * self.shard_count
        self._locks = [threading.Lock() for _ in range(self.shard_count)]

    def increment(self, by: int = 1) -> None:
        """Pick a random shard and add to it (low contention)."""
        idx = random.randrange(self.shard_count)
        with self._locks[idx]:
            self._shards[idx] += by

    def total(self) -> int:
        """Sum every shard for an eventually-consistent read."""
        return sum(self._shards)


def writer(counter: ShardedCounter, n: int) -> None:
    """Hammer the counter with `n` increments."""
    for _ in range(n):
        counter.increment()


def main() -> None:
    """Run 8 writer threads × 50k increments and verify totals."""
    counter = ShardedCounter(shard_count=16)
    threads = [
        threading.Thread(target=writer, args=(counter, 50_000)) for _ in range(8)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    expected = 8 * 50_000
    actual = counter.total()
    print(f"expected total : {expected:,}")
    print(f"actual total   : {actual:,}")
    print(f"shard sizes    : {counter._shards}")
    print(f"max-min spread : {max(counter._shards) - min(counter._shards):,}")
    assert actual == expected, "sharded counter lost increments"


if __name__ == "__main__":
    main()
