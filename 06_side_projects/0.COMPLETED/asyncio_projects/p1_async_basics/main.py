"""P1: Asyncio basics.

Run this file to see the difference between sequential waiting and concurrent
waiting. Nothing here is about speed of CPU work. The win comes from letting
other tasks run while one task is waiting.
"""

from __future__ import annotations

import asyncio
import time


async def make_coffee(name: str, seconds: float) -> str:
    """Pretend to make one coffee order while the program waits asynchronously."""
    print(f"start  {name}: waiting {seconds:.1f}s")
    await asyncio.sleep(seconds)
    print(f"done   {name}")
    return f"{name} ready"


async def sequential_demo() -> list[str]:
    """Run three coffee orders one after another."""
    results = []
    results.append(await make_coffee("espresso", 1.0))
    results.append(await make_coffee("latte", 1.5))
    results.append(await make_coffee("mocha", 0.8))
    return results


async def concurrent_demo() -> list[str]:
    """Run three coffee orders concurrently with gather."""
    return await asyncio.gather(
        make_coffee("espresso", 1.0),
        make_coffee("latte", 1.5),
        make_coffee("mocha", 0.8),
    )


async def task_demo() -> None:
    """Create a task explicitly, do other work, then await the task result."""
    task = asyncio.create_task(make_coffee("cold brew", 1.0))
    print("cashier: taking the next order while cold brew is waiting")
    await asyncio.sleep(0.2)
    result = await task
    print(f"task result: {result}")


async def main() -> None:
    """Run the three beginner demos in a readable order."""
    print("\n--- sequential: each await waits before the next starts ---")
    start = time.perf_counter()
    print(await sequential_demo())
    print(f"sequential took {time.perf_counter() - start:.2f}s")

    print("\n--- concurrent: gather starts all waits together ---")
    start = time.perf_counter()
    print(await concurrent_demo())
    print(f"concurrent took {time.perf_counter() - start:.2f}s")

    print("\n--- explicit task: schedule now, await later ---")
    await task_demo()


if __name__ == "__main__":
    asyncio.run(main())
