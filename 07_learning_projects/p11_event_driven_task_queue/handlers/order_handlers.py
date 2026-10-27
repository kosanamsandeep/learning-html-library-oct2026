"""
=============================================================================
PROJECT 11: EVENT-DRIVEN TASK QUEUE
=============================================================================
FILE: handlers/order_handlers.py
PURPOSE: Event handlers that react to domain events

HANDLERS are the "subscribers" in Pub/Sub:
- They listen for specific events
- They execute side-effects (send email, update DB, etc.)
- They can enqueue tasks for async processing

SEPARATION OF CONCERNS:
- Models define WHAT happened (Event)
- Bus routes WHERE it goes
- Handlers define WHAT TO DO about it
=============================================================================
"""

from models.event import Event, Task, EventPriority


class OrderEventHandlers:
    """
    Handlers for order-related events.

    Each method is a handler that reacts to a specific event.
    In production, these would call external services, databases, etc.
    """

    def __init__(self):
        """Initialize the object with the dependencies or starting values it needs."""
        self.handled_events: list[dict] = []

    def on_order_placed(self, event: Event) -> None:
        """React to 'order.placed' event."""
        order_id = event.payload.get("order_id", "???")
        customer = event.payload.get("customer", "???")
        total = event.payload.get("total", 0)

        print(f"    [OrderHandler] New order {order_id} from {customer} (${total:.2f})")
        self.handled_events.append(
            {
                "handler": "on_order_placed",
                "event_id": event.event_id,
                "order_id": order_id,
            }
        )

    def on_order_confirmed(self, event: Event) -> None:
        """React to 'order.confirmed' — start fulfillment."""
        order_id = event.payload.get("order_id", "???")
        print(f"    [OrderHandler] Order {order_id} confirmed → Starting fulfillment")
        self.handled_events.append(
            {
                "handler": "on_order_confirmed",
                "event_id": event.event_id,
            }
        )

    def on_order_shipped(self, event: Event) -> None:
        """React to 'order.shipped' — notify customer."""
        order_id = event.payload.get("order_id", "???")
        tracking = event.payload.get("tracking_number", "N/A")
        print(f"    [OrderHandler] Order {order_id} shipped! Tracking: {tracking}")
        self.handled_events.append(
            {
                "handler": "on_order_shipped",
                "event_id": event.event_id,
            }
        )


class NotificationHandlers:
    """Handlers that send notifications in response to events."""

    def __init__(self):
        """Initialize the object with the dependencies or starting values it needs."""
        self.notifications_sent: list[str] = []

    def send_order_confirmation_email(self, event: Event) -> None:
        """Send email when order is placed."""
        email = event.payload.get("customer_email", "unknown@example.com")
        order_id = event.payload.get("order_id", "???")
        print(
            f"    [Notification] 📧 Confirmation email → {email} for order {order_id}"
        )
        self.notifications_sent.append(f"email:{email}:order_confirmed:{order_id}")

    def send_shipping_sms(self, event: Event) -> None:
        """Send SMS when order ships."""
        phone = event.payload.get("customer_phone", "+1-XXX")
        order_id = event.payload.get("order_id", "???")
        print(f"    [Notification] 📱 Shipping SMS → {phone} for order {order_id}")
        self.notifications_sent.append(f"sms:{phone}:shipped:{order_id}")

    def notify_warehouse(self, event: Event) -> None:
        """Notify warehouse to prepare shipment."""
        order_id = event.payload.get("order_id", "???")
        items = event.payload.get("items", [])
        print(
            f"    [Notification] 🏭 Warehouse alert: Prepare {len(items)} items for {order_id}"
        )
        self.notifications_sent.append(f"warehouse:{order_id}")


class AnalyticsHandlers:
    """Handlers that track metrics and analytics."""

    def __init__(self):
        """Initialize the object with the dependencies or starting values it needs."""
        self.metrics: dict = {"orders": 0, "revenue": 0.0, "shipments": 0}

    def track_order(self, event: Event) -> None:
        """Track order placement metrics."""
        self.metrics["orders"] += 1
        self.metrics["revenue"] += event.payload.get("total", 0)

    def track_shipment(self, event: Event) -> None:
        """Track shipment metrics."""
        self.metrics["shipments"] += 1
