"""Small helpers shared across modules."""
from __future__ import annotations

import time
from contextlib import contextmanager


@contextmanager
def timer(label: str = "block"):
    t = time.perf_counter()
    try:
        yield
    finally:
        print(f"[timer] {label}: {time.perf_counter()-t:.3f}s")
