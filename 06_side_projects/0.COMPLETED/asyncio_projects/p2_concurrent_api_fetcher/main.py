"""P2: Concurrent API fetcher.

This project simulates calling several slow APIs. The same pattern applies to
real async HTTP clients such as httpx.AsyncClient or aiohttp.ClientSession, but
this example uses only the standard library so the asyncio idea stays visible.
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class ApiResponse:
    """Small response object returned by the fake remote API."""

    name: str
    latency: float
    payload: dict[str, str]


async def fake_api_call(name: str, latency: float, fail: bool = False) -> ApiResponse:
    """Pretend to call a remote API that responds after a delay."""
    await asyncio.sleep(latency)
    if fail:
        raise RuntimeError(f"{name} failed")
    return ApiResponse(name=name, latency=latency, payload={"status": "ok"})


async def fetch_sequential(endpoints: list[tuple[str, float]]) -> list[ApiResponse]:
    """Fetch endpoints one by one, waiting for each before starting the next."""
    results = []
    for name, latency in endpoints:
        results.append(await fake_api_call(name, latency))
    return results


async def fetch_concurrent(endpoints: list[tuple[str, float]]) -> list[ApiResponse]:
    """Fetch all endpoints at the same time and preserve input order."""
    calls = [fake_api_call(name, latency) for name, latency in endpoints]
    return await asyncio.gather(*calls)


async def fetch_as_completed(endpoints: list[tuple[str, float]]) -> list[str]:
    """Process responses in completion order instead of input order."""
    tasks = [
        asyncio.create_task(fake_api_call(name, latency)) for name, latency in endpoints
    ]
    completed = []
    for task in asyncio.as_completed(tasks):
        response = await task
        completed.append(response.name)
        print(f"received {response.name} after {response.latency:.1f}s")
    return completed


async def fetch_with_timeout(name: str, latency: float, timeout: float) -> str:
    """Cancel a slow call if it does not finish within the timeout."""
    try:
        await asyncio.wait_for(fake_api_call(name, latency), timeout=timeout)
        return f"{name}: success"
    except asyncio.TimeoutError:
        return f"{name}: timed out after {timeout:.1f}s"


async def main() -> None:
    """Run sequential, concurrent, completion-order, and timeout demos."""
    endpoints = [("users", 1.2), ("orders", 0.8), ("payments", 1.5), ("inventory", 0.5)]

    start = time.perf_counter()
    await fetch_sequential(endpoints)
    print(f"sequential took {time.perf_counter() - start:.2f}s")

    start = time.perf_counter()
    await fetch_concurrent(endpoints)
    print(f"concurrent took {time.perf_counter() - start:.2f}s")

    print("\ncompletion order:")
    await fetch_as_completed(endpoints)

    print("\ntimeout example:")
    print(await fetch_with_timeout("slow-reports", latency=2.0, timeout=0.7))


if __name__ == "__main__":
    random.seed(7)
    asyncio.run(main())
