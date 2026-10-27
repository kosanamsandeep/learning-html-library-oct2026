"""Small library used to demo property-based testing in P9.

Each function has a few example-based tests and a few property-based ones.
The properties are written as 'things that must always be true', not 'this
specific input gives this specific output'.
"""

from __future__ import annotations

import base64


def reverse(s: str) -> str:
    return s[::-1]


def base64_round_trip(data: bytes) -> bytes:
    """Encode to base64, then decode back. Should always return the original."""
    encoded = base64.b64encode(data)
    return base64.b64decode(encoded)


def merge_sorted(a: list[int], b: list[int]) -> list[int]:
    """Merge two already-sorted lists into a sorted list."""
    out: list[int] = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            out.append(a[i])
            i += 1
        else:
            out.append(b[j])
            j += 1
    out.extend(a[i:])
    out.extend(b[j:])
    return out


def safe_average(numbers: list[float]) -> float | None:
    """Average of a list, or None if the list is empty."""
    if not numbers:
        return None
    return sum(numbers) / len(numbers)
