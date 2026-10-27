"""P5 Fundamentals · URL Shortener (Bitly-style).

The classic 5-line system design interview question. You need:
  - A way to turn a long URL into a short code that fits in a tweet.
  - A way to map the short code back to the original URL very fast.
  - A strategy for collisions (different inputs mapping to the same code).

This file builds two versions:
  - Hash-based (deterministic, idempotent for the same URL).
  - Counter-based (monotonic ids, no collisions, but reveals creation order).
"""

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass, field

BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def to_base62(n: int) -> str:
    """Encode a non-negative integer to a compact base62 string."""
    if n == 0:
        return BASE62[0]
    out = []
    while n > 0:
        n, rem = divmod(n, 62)
        out.append(BASE62[rem])
    return "".join(reversed(out))


@dataclass
class HashShortener:
    """Deterministic shortener: same URL always gets the same code."""

    code_length: int = 7
    _store: dict[str, str] = field(default_factory=dict)

    def shorten(self, url: str) -> str:
        """Return a short code; on collision, lengthen the slice until unique."""
        digest = hashlib.sha256(url.encode()).hexdigest()
        for length in range(self.code_length, len(digest)):
            code = digest[:length]
            existing = self._store.get(code)
            if existing is None:
                self._store[code] = url
                return code
            if existing == url:
                return code  # same URL re-shortened
        raise RuntimeError("could not allocate a unique code")

    def resolve(self, code: str) -> str | None:
        """Return the original URL for `code` or None if unknown."""
        return self._store.get(code)


@dataclass
class CounterShortener:
    """Monotonic id + base62 encode; no collisions but predictable."""

    _next_id: int = 1_000_000  # start high so codes are at least a few chars
    _store: dict[str, str] = field(default_factory=dict)
    _reverse: dict[str, str] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def shorten(self, url: str) -> str:
        """Allocate the next id, encode it, and remember both directions."""
        with self._lock:
            if url in self._reverse:
                return self._reverse[url]
            code = to_base62(self._next_id)
            self._next_id += 1
            self._store[code] = url
            self._reverse[url] = code
            return code

    def resolve(self, code: str) -> str | None:
        """Return the original URL for `code` or None if unknown."""
        return self._store.get(code)


def main() -> None:
    """Show both strategies on a few example URLs."""
    urls = [
        "https://example.com/articles/how-rate-limiters-work",
        "https://example.com/articles/how-rate-limiters-work",  # dup
        "https://example.com/blog/consistent-hashing-explained",
        "https://example.com/very/long/path/with?query=params&plenty=true",
    ]

    print("--- Hash-based shortener ---")
    hs = HashShortener()
    for u in urls:
        code = hs.shorten(u)
        print(f"  {code:>10s}  ->  {u}")

    print("\n--- Counter-based shortener ---")
    cs = CounterShortener()
    for u in urls:
        code = cs.shorten(u)
        print(f"  {code:>10s}  ->  {u}")

    # Verify resolve round-trip on the counter version.
    sample = cs.shorten(urls[0])
    print(f"\nresolve('{sample}') -> {cs.resolve(sample)}")


if __name__ == "__main__":
    main()
