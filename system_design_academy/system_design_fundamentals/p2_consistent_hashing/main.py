"""P2 Fundamentals · Consistent Hashing.

When you have N cache servers and you hash key % N to pick one, adding a single
server reshuffles nearly all keys. Consistent hashing fixes this by placing
servers on a circular ring of hash slots. Adding or removing a server only
moves keys assigned to the affected slice.

This file implements a simple ring with virtual nodes and demonstrates the
re-mapping cost when you add or remove a server.
"""

from __future__ import annotations

import hashlib
import random
from bisect import bisect_right
from dataclasses import dataclass, field


def _hash(value: str) -> int:
    """Stable 64-bit-ish integer hash from MD5 (good enough for teaching)."""
    return int(hashlib.md5(value.encode()).hexdigest()[:16], 16)


@dataclass
class ConsistentHashRing:
    """Hash ring with virtual nodes per real server."""

    replicas: int = 100
    _ring: list[int] = field(default_factory=list)
    _slot_to_node: dict[int, str] = field(default_factory=dict)

    def add_node(self, name: str) -> None:
        """Register `replicas` virtual nodes for one server."""
        for i in range(self.replicas):
            slot = _hash(f"{name}#{i}")
            self._slot_to_node[slot] = name
            self._ring.append(slot)
        self._ring.sort()

    def remove_node(self, name: str) -> None:
        """Remove all virtual nodes belonging to one server."""
        keep = [s for s in self._ring if self._slot_to_node[s] != name]
        for s in self._ring:
            if self._slot_to_node[s] == name:
                del self._slot_to_node[s]
        self._ring = keep

    def get_node(self, key: str) -> str:
        """Return the server responsible for this key (first slot clockwise)."""
        if not self._ring:
            raise RuntimeError("ring is empty")
        slot = _hash(key)
        index = bisect_right(self._ring, slot) % len(self._ring)
        return self._slot_to_node[self._ring[index]]


def fraction_remapped(before: dict[str, str], after: dict[str, str]) -> float:
    """Return the fraction of keys whose owning server changed."""
    moved = sum(1 for k, v in before.items() if after[k] != v)
    return moved / len(before)


def main() -> None:
    """Show that adding a node only re-maps a small fraction of keys."""
    random.seed(42)
    keys = [f"user:{i}" for i in range(10_000)]

    ring = ConsistentHashRing(replicas=150)
    for name in ["cache-a", "cache-b", "cache-c"]:
        ring.add_node(name)

    before = {k: ring.get_node(k) for k in keys}
    distribution = {
        n: sum(1 for v in before.values() if v == n)
        for n in {"cache-a", "cache-b", "cache-c"}
    }
    print(f"3 nodes distribution: {distribution}")

    ring.add_node("cache-d")
    after_add = {k: ring.get_node(k) for k in keys}
    print(
        f"after adding cache-d, fraction of keys remapped: {fraction_remapped(before, after_add):.2%}"
    )

    ring.remove_node("cache-b")
    after_remove = {k: ring.get_node(k) for k in keys}
    print(
        f"after removing cache-b, fraction of keys remapped vs prior step: {fraction_remapped(after_add, after_remove):.2%}"
    )

    distribution = {
        n: sum(1 for v in after_remove.values() if v == n)
        for n in {"cache-a", "cache-c", "cache-d"}
    }
    print(f"final distribution: {distribution}")


if __name__ == "__main__":
    main()
