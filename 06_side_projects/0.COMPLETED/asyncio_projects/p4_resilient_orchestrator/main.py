"""P4: Resilient async orchestrator.

This project demonstrates production async controls: limit concurrency with a
semaphore, retry unreliable calls, apply timeouts, and use TaskGroup so related
tasks succeed or fail as one structured unit.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceCall:
    """Configuration for one downstream service call."""

    name: str
    latency: float
    failure_rate: float


async def unreliable_call(call: ServiceCall) -> str:
    """Pretend to call a downstream service that may fail."""
    await asyncio.sleep(call.latency)
    if random.random() < call.failure_rate:
        raise RuntimeError(f"{call.name} temporary failure")
    return f"{call.name}: ok"


async def call_with_retry(call: ServiceCall, retries: int = 2) -> str:
    """Retry a flaky call with small exponential backoff."""
    for attempt in range(1, retries + 2):
        try:
            return await asyncio.wait_for(unreliable_call(call), timeout=1.2)
        except (RuntimeError, asyncio.TimeoutError) as exc:
            if attempt > retries:
                return f"{call.name}: failed after {attempt} attempts ({exc})"
            backoff = 0.2 * attempt
            print(f"{call.name}: attempt {attempt} failed; retrying in {backoff:.1f}s")
            await asyncio.sleep(backoff)
    raise AssertionError("unreachable")


async def guarded_call(call: ServiceCall, semaphore: asyncio.Semaphore) -> str:
    """Run one call while respecting the global concurrency limit."""
    async with semaphore:
        return await call_with_retry(call)


async def orchestrate_dashboard() -> dict[str, str]:
    """Fan out to multiple services while limiting concurrency and collecting results."""
    random.seed(11)
    calls = [
        ServiceCall("profile", 0.4, 0.1),
        ServiceCall("orders", 0.8, 0.3),
        ServiceCall("payments", 0.5, 0.4),
        ServiceCall("recommendations", 0.9, 0.2),
        ServiceCall("inventory", 0.3, 0.1),
    ]
    semaphore = asyncio.Semaphore(2)
    results: dict[str, str] = {}

    async with asyncio.TaskGroup() as group:
        task_map = {
            group.create_task(guarded_call(call, semaphore)): call.name
            for call in calls
        }

    for task, name in task_map.items():
        results[name] = task.result()
    return results


async def cancellation_demo() -> None:
    """Show how cancellation asks a task to stop at the next await point."""

    async def long_running_report() -> None:
        """Pretend to build a report until cancelled."""
        try:
            while True:
                print("report: still working...")
                await asyncio.sleep(0.4)
        except asyncio.CancelledError:
            print("report: cleanup before stopping")
            raise

    task = asyncio.create_task(long_running_report())
    await asyncio.sleep(1.0)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


async def main() -> None:
    """Run the resilient orchestration and cancellation demos."""
    print("dashboard orchestration:")
    results = await orchestrate_dashboard()
    for name, result in results.items():
        print(f"  {name}: {result}")

    print("\ncancellation demo:")
    await cancellation_demo()


if __name__ == "__main__":
    asyncio.run(main())
