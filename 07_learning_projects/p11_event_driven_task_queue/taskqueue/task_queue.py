"""
=============================================================================
PROJECT 11: EVENT-DRIVEN TASK QUEUE
=============================================================================
FILE: queue/task_queue.py
PURPOSE: Priority Task Queue with worker dispatch

COMMAND PATTERN:
- Each task encapsulates a request as an object
- Tasks are queued and executed later by workers
- Supports priority ordering, retries, dead-letter queue

GOLDEN STANDARD: Mirrors Celery's task lifecycle:
    PENDING → RECEIVED → STARTED → SUCCESS/FAILURE/RETRY
=============================================================================
"""

import heapq
from datetime import datetime
from typing import Callable, Any

from models.event import Task, TaskStatus, EventPriority

# Type alias: a worker function takes a Task and returns a result
TaskWorker = Callable[[Task], Any]


class TaskQueue:
    """
    Priority-based task queue with worker registration and dispatch.

    INTERNAL DATA STRUCTURE: Min-heap (heapq)
    - Tasks are ordered by priority (higher priority = processed first)
    - Same priority → FIFO order (earlier tasks first)

    DESIGN DECISIONS:
    - Workers register for specific task types (like Celery @app.task)
    - Queue dispatches to the right worker based on task_type
    - Failed tasks retry with exponential backoff
    - Dead tasks go to dead-letter queue for manual inspection
    """

    def __init__(self):
        # Priority queue: (negative_priority, insertion_order, task)
        # Negative because heapq is min-heap; we want highest priority first
        """Initialize the object with the dependencies or starting values it needs."""
        self._queue: list[tuple[int, int, Task]] = []
        self._insertion_counter: int = 0

        # Worker registry: task_type → worker function
        self._workers: dict[str, TaskWorker] = {}

        # Tracking
        self._completed: list[Task] = []
        self._dead_letter: list[Task] = []
        self._processing: dict[str, Task] = {}  # task_id → task

    def register_worker(self, task_type: str, worker: TaskWorker) -> None:
        """
        Register a worker function for a task type.

        ANALOGY: Like Celery's @app.task decorator:
            @app.task
            def send_email(to, subject, body): ...

        Here:
            queue.register_worker("send_email", send_email_func)
        """
        self._workers[task_type] = worker

    def enqueue(self, task: Task) -> str:
        """
        Add a task to the queue.

        Returns the task_id for tracking.
        Tasks are ordered by priority (CRITICAL first, LOW last).
        """
        # Use negative priority so highest priority pops first from min-heap
        priority_value = -task.priority.value
        heapq.heappush(self._queue, (priority_value, self._insertion_counter, task))
        self._insertion_counter += 1
        return task.task_id

    def enqueue_many(self, tasks: list[Task]) -> list[str]:
        """Enqueue multiple tasks. Returns list of task_ids."""
        return [self.enqueue(task) for task in tasks]

    def dequeue(self) -> Task | None:
        """
        Pop the highest-priority task from the queue.
        Returns None if queue is empty.
        """
        if not self._queue:
            return None
        _, _, task = heapq.heappop(self._queue)
        return task

    def process_next(self) -> Task | None:
        """
        Dequeue and execute the next task.

        FLOW:
        1. Pop highest-priority task
        2. Find registered worker for task_type
        3. Execute worker with the task
        4. Handle success/failure/retry
        """
        task = self.dequeue()
        if task is None:
            return None

        # Find worker
        worker = self._workers.get(task.task_type)
        if worker is None:
            task.mark_dead(f"No worker registered for task_type: {task.task_type}")
            self._dead_letter.append(task)
            return task

        # Execute
        task.mark_processing()
        self._processing[task.task_id] = task

        try:
            result = worker(task)
            task.mark_completed(result)
            self._completed.append(task)
        except Exception as e:
            task.mark_failed(str(e))
            if task.status == TaskStatus.RETRYING:
                # Re-enqueue for retry
                self.enqueue(task)
            else:
                # Dead — max retries exhausted
                self._dead_letter.append(task)
        finally:
            self._processing.pop(task.task_id, None)

        return task

    def process_all(self) -> list[Task]:
        """Process all tasks in the queue until empty."""
        results = []
        while self._queue:
            task = self.process_next()
            if task:
                results.append(task)
        return results

    def size(self) -> int:
        """Number of tasks waiting in queue."""
        return len(self._queue)

    def get_completed(self) -> list[Task]:
        """Return the requested item or information if it exists."""
        return self._completed.copy()

    def get_dead_letters(self) -> list[Task]:
        """Return the requested item or information if it exists."""
        return self._dead_letter.copy()

    def get_stats(self) -> dict:
        """Return queue statistics."""
        return {
            "pending": len(self._queue),
            "processing": len(self._processing),
            "completed": len(self._completed),
            "dead_letter": len(self._dead_letter),
            "registered_workers": list(self._workers.keys()),
        }
