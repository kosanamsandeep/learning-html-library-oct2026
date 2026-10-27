"""P3: Async producer/consumer pipeline.

A producer creates jobs, workers consume them from an asyncio.Queue, and the
queue provides backpressure when producers are faster than consumers.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    """One unit of work flowing through the async pipeline."""

    job_id: int
    customer: str
    work_seconds: float


async def producer(queue: asyncio.Queue[Job], total_jobs: int) -> None:
    """Create jobs and put them into the queue, waiting if the queue is full."""
    for job_id in range(1, total_jobs + 1):
        job = Job(
            job_id=job_id,
            customer=f"customer-{job_id}",
            work_seconds=random.uniform(0.2, 0.8),
        )
        await queue.put(job)
        print(f"produced job {job.job_id}; queue size={queue.qsize()}")
        await asyncio.sleep(0.1)


async def worker(name: str, queue: asyncio.Queue[Job]) -> None:
    """Continuously take jobs from the queue until cancelled by the coordinator."""
    try:
        while True:
            job = await queue.get()
            try:
                print(f"{name} started job {job.job_id}")
                await asyncio.sleep(job.work_seconds)
                print(f"{name} finished job {job.job_id}")
            finally:
                queue.task_done()
    except asyncio.CancelledError:
        print(f"{name} shutting down")
        raise


async def run_pipeline(total_jobs: int = 10, worker_count: int = 3) -> None:
    """Start producer and workers, wait for all jobs, then stop workers."""
    queue: asyncio.Queue[Job] = asyncio.Queue(maxsize=4)
    workers = [
        asyncio.create_task(worker(f"worker-{i}", queue))
        for i in range(1, worker_count + 1)
    ]

    await producer(queue, total_jobs)
    print("producer done; waiting for queue to drain")
    await queue.join()

    for task in workers:
        task.cancel()
    await asyncio.gather(*workers, return_exceptions=True)
    print("pipeline complete")


async def main() -> None:
    """Run the queue worker pipeline demo."""
    random.seed(3)
    await run_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
