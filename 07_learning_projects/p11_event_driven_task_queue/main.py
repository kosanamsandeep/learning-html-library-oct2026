"""
=============================================================================
PROJECT 11: EVENT-DRIVEN TASK QUEUE — MAIN DEMO
=============================================================================
Demonstrates: Event Bus (Pub/Sub), Task Queue (Command Pattern),
              Workers, Handlers, Priority Processing, Retry Logic

RUN: cd p11_event_driven_task_queue && python main.py
=============================================================================
"""

import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.event import Event, Task, EventPriority, TaskStatus
from bus.event_bus import EventBus
from taskqueue.task_queue import TaskQueue
from handlers.order_handlers import (
    OrderEventHandlers,
    NotificationHandlers,
    AnalyticsHandlers,
)
from workers.task_workers import (
    send_email_worker,
    process_payment_worker,
    generate_invoice_worker,
    update_inventory_worker,
    send_webhook_worker,
)


def print_header(title: str) -> None:
    """Perform the print header step used by this project."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_event_bus():
    """DEMO 1: Event Bus — Pub/Sub pattern."""
    print_header("DEMO 1: Event Bus (Publisher/Subscriber)")

    bus = EventBus()

    # Initialize handlers
    order_handlers = OrderEventHandlers()
    notification_handlers = NotificationHandlers()
    analytics_handlers = AnalyticsHandlers()

    # SUBSCRIBE: Multiple handlers for same event
    print("\n  Subscribing handlers to events:")
    bus.subscribe("order.placed", order_handlers.on_order_placed)
    bus.subscribe("order.placed", notification_handlers.send_order_confirmation_email)
    bus.subscribe("order.placed", notification_handlers.notify_warehouse)
    bus.subscribe("order.placed", analytics_handlers.track_order)
    bus.subscribe("order.confirmed", order_handlers.on_order_confirmed)
    bus.subscribe("order.shipped", order_handlers.on_order_shipped)
    bus.subscribe("order.shipped", notification_handlers.send_shipping_sms)
    bus.subscribe("order.shipped", analytics_handlers.track_shipment)
    print(f"    Registered event types: {bus.get_all_event_types()}")

    # PUBLISH: Emit events
    print("\n  Publishing 'order.placed' event:")
    event1 = Event(
        event_type="order.placed",
        payload={
            "order_id": "ORD-001",
            "customer": "Alice",
            "customer_email": "alice@example.com",
            "total": 149.99,
            "items": [{"name": "Keyboard", "qty": 1}, {"name": "Mouse", "qty": 2}],
        },
        source="checkout_service",
    )
    handlers_called = bus.publish(event1)
    print(f"    → {handlers_called} handlers processed the event")

    print("\n  Publishing 'order.shipped' event:")
    event2 = Event(
        event_type="order.shipped",
        payload={
            "order_id": "ORD-001",
            "customer_phone": "+1-555-1234",
            "tracking_number": "UPS-789456123",
        },
        source="shipping_service",
    )
    handlers_called = bus.publish(event2)
    print(f"    → {handlers_called} handlers processed the event")

    # Dead letter: event with no subscribers
    print("\n  Publishing event with NO subscribers:")
    orphan = Event(event_type="inventory.low", payload={"sku": "KB-001"})
    handlers_called = bus.publish(orphan)
    print(f"    → {handlers_called} handlers (goes to dead-letter queue)")
    print(f"    Dead letters: {len(bus.get_dead_letters())}")

    # Analytics
    print(f"\n  Analytics metrics: {analytics_handlers.metrics}")


def demo_task_queue():
    """DEMO 2: Task Queue with Workers — Command Pattern."""
    print_header("DEMO 2: Task Queue (Command Pattern + Workers)")

    queue = TaskQueue()

    # Register workers
    print("\n  Registering workers:")
    queue.register_worker("send_email", send_email_worker)
    queue.register_worker("process_payment", process_payment_worker)
    queue.register_worker("generate_invoice", generate_invoice_worker)
    queue.register_worker("update_inventory", update_inventory_worker)
    queue.register_worker("send_webhook", send_webhook_worker)
    print(f"    Workers: {queue.get_stats()['registered_workers']}")

    # Enqueue tasks with different priorities
    print("\n  Enqueueing tasks with priorities:")
    tasks = [
        Task(
            task_type="process_payment",
            priority=EventPriority.CRITICAL,
            payload={"amount": 149.99, "method": "visa", "order_id": "ORD-001"},
        ),
        Task(
            task_type="send_email",
            priority=EventPriority.NORMAL,
            payload={
                "to": "alice@example.com",
                "subject": "Order Confirmed",
                "body": "Thanks!",
            },
        ),
        Task(
            task_type="generate_invoice",
            priority=EventPriority.LOW,
            payload={"order_id": "ORD-001", "customer": "Alice", "total": 149.99},
        ),
        Task(
            task_type="update_inventory",
            priority=EventPriority.HIGH,
            payload={
                "items": [{"name": "Keyboard", "qty": 1}, {"name": "Mouse", "qty": 2}]
            },
        ),
        Task(
            task_type="send_webhook",
            priority=EventPriority.NORMAL,
            payload={"url": "https://partner.api/orders", "event_type": "order.placed"},
        ),
    ]

    for task in tasks:
        queue.enqueue(task)
        print(f"    Enqueued: {task.task_type} (priority: {task.priority.name})")

    print(f"\n  Queue size: {queue.size()}")
    print("  Processing all tasks (highest priority first):\n")

    # Seed random for reproducible demo
    random.seed(42)

    results = queue.process_all()
    print(f"\n  Results:")
    for task in results:
        status_icon = "✅" if task.status == TaskStatus.COMPLETED else "❌"
        print(f"    {status_icon} {task.task_type} → {task.status.value}")
        if task.error:
            print(f"       Error: {task.error} (retries: {task.retry_count})")

    stats = queue.get_stats()
    print(f"\n  Final stats: {stats}")


def demo_priority_ordering():
    """DEMO 3: Priority queue ordering."""
    print_header("DEMO 3: Priority Ordering")

    queue = TaskQueue()
    queue.register_worker(
        "log",
        lambda t: print(
            f"    Processing: {t.payload['msg']} (priority: {t.priority.name})"
        ),
    )

    # Enqueue in random order
    print("\n  Enqueueing tasks in random priority order:")
    priorities = [
        (EventPriority.LOW, "Low priority backup job"),
        (EventPriority.CRITICAL, "CRITICAL: System alert"),
        (EventPriority.NORMAL, "Normal: Send weekly report"),
        (EventPriority.HIGH, "High: Process refund"),
        (EventPriority.NORMAL, "Normal: Update cache"),
        (EventPriority.CRITICAL, "CRITICAL: Security breach"),
    ]

    for priority, msg in priorities:
        task = Task(task_type="log", priority=priority, payload={"msg": msg})
        queue.enqueue(task)
        print(f"    + {msg}")

    print("\n  Processing (should be CRITICAL → HIGH → NORMAL → LOW):\n")
    queue.process_all()


def demo_retry_logic():
    """DEMO 4: Task retry with backoff."""
    print_header("DEMO 4: Retry Logic (Fault Tolerance)")

    queue = TaskQueue()

    # Worker that always fails
    attempt = [0]

    def flaky_worker(task: Task) -> dict:
        """Perform the flaky worker step used by this project."""
        attempt[0] += 1
        if attempt[0] <= 3:
            raise ConnectionError(f"Connection refused (attempt {attempt[0]})")
        return {"status": "finally succeeded!"}

    queue.register_worker("flaky_job", flaky_worker)

    task = Task(
        task_type="flaky_job", max_retries=3, payload={"action": "connect_to_db"}
    )
    queue.enqueue(task)

    print(f"\n  Task: {task.task_type} (max_retries={task.max_retries})")
    print("  Processing with retries:\n")

    # Process multiple times (retries re-enqueue)
    for i in range(5):
        if queue.size() == 0:
            break
        result = queue.process_next()
        if result:
            print(
                f"    Attempt {i+1}: status={result.status.value}, retries={result.retry_count}, error={result.error}"
            )

    print(f"\n  Dead letter queue: {len(queue.get_dead_letters())} tasks")
    print(f"  Completed: {len(queue.get_completed())} tasks")


def demo_event_to_task_bridge():
    """DEMO 5: Events triggering tasks (bridging both patterns)."""
    print_header("DEMO 5: Event → Task Bridge (Real-World Pattern)")

    bus = EventBus()
    queue = TaskQueue()

    # Register workers
    queue.register_worker("send_email", send_email_worker)
    queue.register_worker("process_payment", process_payment_worker)
    queue.register_worker("update_inventory", update_inventory_worker)

    # Bridge: Event handler that creates tasks
    def on_order_placed_create_tasks(event: Event):
        """This handler BRIDGES events to tasks."""
        print(f"    [Bridge] order.placed → Creating 3 async tasks")
        queue.enqueue(
            Task(
                task_type="process_payment",
                priority=EventPriority.CRITICAL,
                payload={
                    "amount": event.payload["total"],
                    "method": "card",
                    "order_id": event.payload["order_id"],
                },
            )
        )
        queue.enqueue(
            Task(
                task_type="send_email",
                priority=EventPriority.NORMAL,
                payload={
                    "to": event.payload["customer_email"],
                    "subject": "Order Received!",
                    "body": "We got your order.",
                },
            )
        )
        queue.enqueue(
            Task(
                task_type="update_inventory",
                priority=EventPriority.HIGH,
                payload={"items": event.payload.get("items", [])},
            )
        )

    bus.subscribe("order.placed", on_order_placed_create_tasks)

    # Publish event
    print("\n  Publishing 'order.placed' event:")
    order_event = Event(
        event_type="order.placed",
        payload={
            "order_id": "ORD-042",
            "customer_email": "bob@company.com",
            "total": 299.99,
            "items": [{"name": "Monitor", "qty": 1}],
        },
    )
    bus.publish(order_event)
    print(f"\n  Tasks in queue: {queue.size()}")

    # Process all tasks
    random.seed(99)
    print("\n  Processing tasks:\n")
    queue.process_all()

    print(f"\n  ✨ Pattern: Event was fire-and-forget, tasks executed async")
    print(f"     Events decouple, Tasks execute, Queue prioritizes")


def main():
    """Perform the main step used by this project."""
    print("\n" + "█" * 70)
    print("█  PROJECT 11: EVENT-DRIVEN TASK QUEUE                              █")
    print("█  Patterns: Observer, Pub/Sub, Command, Priority Queue             █")
    print("█  Inspired by: Celery, RabbitMQ, Django Signals, AWS SQS           █")
    print("█" * 70)

    demo_event_bus()
    demo_task_queue()
    demo_priority_ordering()
    demo_retry_logic()
    demo_event_to_task_bridge()

    print_header("LEARNING SUMMARY")
    print("""
  📡 EVENT BUS (Pub/Sub + Observer):
     - Publishers emit events without knowing subscribers
     - Multiple handlers per event type
     - Dead-letter queue for unhandled events

  📋 TASK QUEUE (Command Pattern):
     - Tasks encapsulate work as objects
     - Priority ordering (CRITICAL → HIGH → NORMAL → LOW)
     - Workers registered per task_type

  🔄 RETRY LOGIC:
     - Failed tasks automatically retry (max_retries)
     - Dead-letter queue for permanently failed tasks
     - Exponential backoff in production

  🌉 EVENT → TASK BRIDGE:
     - Events trigger task creation (real-world pattern)
     - Events are synchronous notifications
     - Tasks are asynchronous work units

  🏗️ GOLDEN STANDARDS REFERENCED:
     - Celery: Task queue with workers
     - RabbitMQ/Kafka: Event routing
     - Django Signals: Pub/Sub within app
     - AWS SQS: Dead-letter queues
    """)


if __name__ == "__main__":
    main()
