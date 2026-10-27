"""
=============================================================================
PROJECT 11: EVENT-DRIVEN TASK QUEUE
=============================================================================
FILE: workers/task_workers.py
PURPOSE: Worker functions that process tasks from the queue

WORKERS are like Celery task functions:
- Registered for a specific task_type
- Receive a Task object
- Execute the work
- Return a result or raise an exception

COMMAND PATTERN: Each task is a command object that encapsulates
all info needed to execute an action later.
=============================================================================
"""

import random
from models.event import Task


def send_email_worker(task: Task) -> dict:
    """
    Worker: Sends an email (simulated).
    Registered for task_type: "send_email"
    """
    to = task.payload.get("to", "")
    subject = task.payload.get("subject", "")
    body = task.payload.get("body", "")

    # Simulate occasional failures (20% chance)
    if random.random() < 0.2:
        raise ConnectionError(f"SMTP connection failed for {to}")

    print(f"    [Worker:send_email] ✉️  Sent '{subject}' to {to}")
    return {"status": "sent", "to": to, "subject": subject}


def process_payment_worker(task: Task) -> dict:
    """
    Worker: Processes a payment (simulated).
    Registered for task_type: "process_payment"
    """
    amount = task.payload.get("amount", 0)
    method = task.payload.get("method", "card")
    order_id = task.payload.get("order_id", "???")

    # Simulate payment gateway
    if amount <= 0:
        raise ValueError(f"Invalid payment amount: {amount}")

    print(
        f"    [Worker:process_payment] 💳 Charged ${amount:.2f} via {method} for {order_id}"
    )
    return {
        "status": "charged",
        "amount": amount,
        "transaction_id": f"TXN-{random.randint(1000,9999)}",
    }


def generate_invoice_worker(task: Task) -> dict:
    """
    Worker: Generates an invoice PDF (simulated).
    Registered for task_type: "generate_invoice"
    """
    order_id = task.payload.get("order_id", "???")
    customer = task.payload.get("customer", "???")
    total = task.payload.get("total", 0)

    print(
        f"    [Worker:generate_invoice] 📄 Invoice for {customer} — Order {order_id} — ${total:.2f}"
    )
    return {"status": "generated", "invoice_url": f"/invoices/{order_id}.pdf"}


def update_inventory_worker(task: Task) -> dict:
    """
    Worker: Updates inventory counts (simulated).
    Registered for task_type: "update_inventory"
    """
    items = task.payload.get("items", [])
    for item in items:
        print(
            f"    [Worker:update_inventory] 📦 Reserved {item.get('qty', 1)}x {item.get('name', '?')}"
        )
    return {"status": "updated", "items_reserved": len(items)}


def send_webhook_worker(task: Task) -> dict:
    """
    Worker: Fires a webhook to external system (simulated).
    Registered for task_type: "send_webhook"
    """
    url = task.payload.get("url", "")
    event_type = task.payload.get("event_type", "")

    # Simulate occasional timeout
    if random.random() < 0.15:
        raise TimeoutError(f"Webhook timeout: {url}")

    print(f"    [Worker:send_webhook] 🌐 POST {url} ({event_type})")
    return {"status": "delivered", "url": url}
