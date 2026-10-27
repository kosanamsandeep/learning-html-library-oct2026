"""
=============================================================================
PROJECT 4: E-COMMERCE API
=============================================================================
FILE: models/order.py
PURPOSE: Order domain model
=============================================================================
"""

from datetime import datetime


class OrderItem:
    """Single item in an order."""

    def __init__(
        self, product_id: str, product_name: str, quantity: int, unit_price: float
    ) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self.product_id = product_id
        self.product_name = product_name
        self.quantity = quantity
        self.unit_price = unit_price

    def get_subtotal(self) -> float:
        """Return the requested item or information if it exists."""
        return self.quantity * self.unit_price


class Order:
    """
    Order domain model.
    Contains business logic for order processing.
    """

    def __init__(self, order_id: str, customer_name: str, customer_email: str) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self.order_id = order_id
        self.customer_name = customer_name
        self.customer_email = customer_email
        self.items: list[OrderItem] = []
        self.status: str = (
            "PENDING"  # PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED
        )
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()

    def add_item(
        self, product_id: str, product_name: str, quantity: int, unit_price: float
    ) -> None:
        """Add an item to the order."""
        item = OrderItem(product_id, product_name, quantity, unit_price)
        self.items.append(item)
        self.updated_at = datetime.now()

    def get_total(self) -> float:
        """Calculate order total."""
        return sum(item.get_subtotal() for item in self.items)

    def get_item_count(self) -> int:
        """Total number of items (sum of quantities)."""
        return sum(item.quantity for item in self.items)

    def confirm(self) -> bool:
        """Perform the confirm step used by this project."""
        if self.status != "PENDING":
            return False
        self.status = "CONFIRMED"
        self.updated_at = datetime.now()
        return True

    def cancel(self) -> bool:
        """Perform the cancel step used by this project."""
        if self.status in ("SHIPPED", "DELIVERED"):
            return False  # Too late to cancel
        self.status = "CANCELLED"
        self.updated_at = datetime.now()
        return True
