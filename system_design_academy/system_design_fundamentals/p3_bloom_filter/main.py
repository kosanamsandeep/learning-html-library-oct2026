"""P3 Fundamentals · Bloom Filter.

A bloom filter answers "have I seen this before?" with two possible answers:
  - "definitely no"
  - "maybe yes" (small false positive rate)

It costs a tiny fixed number of bits per item, far less than a hash set.
Famous uses: web crawlers checking "did I already crawl this URL?", databases
checking "is this key worth a disk read?", and bitcoin filters.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field


def _double_hash(item: str, seed: int) -> int:
    """Return an integer hash that varies with `seed`."""
    digest = hashlib.sha256(f"{seed}:{item}".encode()).hexdigest()
    return int(digest[:16], 16)


@dataclass
class BloomFilter:
    """Bit array + k hash functions; supports add and probable membership test."""

    expected_items: int
    false_positive_rate: float = 0.01
    size: int = field(init=False)
    hash_count: int = field(init=False)
    bits: bytearray = field(init=False)

    def __post_init__(self) -> None:
        """Pick size and number of hashes from standard bloom filter math."""
        n, p = self.expected_items, self.false_positive_rate
        self.size = max(8, int(-(n * math.log(p)) / (math.log(2) ** 2)))
        self.hash_count = max(1, int((self.size / n) * math.log(2)))
        self.bits = bytearray((self.size + 7) // 8)

    def _positions(self, item: str) -> list[int]:
        """Return the k bit positions this item maps to."""
        return [_double_hash(item, seed) % self.size for seed in range(self.hash_count)]

    def add(self, item: str) -> None:
        """Set all k bits for this item."""
        for pos in self._positions(item):
            self.bits[pos // 8] |= 1 << (pos % 8)

    def might_contain(self, item: str) -> bool:
        """Return True if every k bit is set (may be a false positive)."""
        for pos in self._positions(item):
            if not (self.bits[pos // 8] & (1 << (pos % 8))):
                return False
        return True


def main() -> None:
    """Insert 5,000 URLs and measure the observed false positive rate."""
    bf = BloomFilter(expected_items=5_000, false_positive_rate=0.01)
    seen = {f"https://site.com/page/{i}" for i in range(5_000)}
    for url in seen:
        bf.add(url)

    # All known URLs must return True.
    for url in seen:
        assert bf.might_contain(url)
    print(f"all {len(seen)} known URLs reported as seen (no false negatives possible)")

    # Probe with 10,000 unseen URLs and count false positives.
    probes = [f"https://site.com/other/{i}" for i in range(10_000)]
    fp = sum(1 for u in probes if bf.might_contain(u))
    print(f"size={bf.size} bits, hashes={bf.hash_count}")
    print(
        f"false positives: {fp} / {len(probes)} = {fp / len(probes):.3%} (target <= 1%)"
    )


if __name__ == "__main__":
    main()
