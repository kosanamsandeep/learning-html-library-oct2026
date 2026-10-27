"""
=============================================================================
PROJECT 4: E-COMMERCE API
=============================================================================
FILE: dtos/order_dto.py
PURPOSE: DTOs for Order operations
=============================================================================
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class OrderItemDTO:
    """DTO for a single order item."""

    product_id: str
    quantity: int

    def validate(self) -> list[str]:
        """Perform the validate step used by this project."""
        errors: list[str] = []
        if not self.product_id:
            errors.append("Product ID is required")
        if self.quantity <= 0:
            errors.append("Quantity must be at least 1")
        return errors


@dataclass
class CreateOrderDTO:
    """
    DTO for creating a new order.

    CLIENT SENDS: customer info + list of items
    SERVER GENERATES: order_id, timestamps, total calculation
    """

    customer_name: str
    customer_email: str
    items: list[OrderItemDTO]

    def validate(self) -> list[str]:
        """Validate the entire order request."""
        errors: list[str] = []

        if not self.customer_name or not self.customer_name.strip():
            errors.append("Customer name is required")

        if not self.customer_email or "@" not in self.customer_email:
            errors.append("Valid email is required")

        if not self.items:
            errors.append("Order must have at least one item")
        else:
            for i, item in enumerate(self.items):
                item_errors = item.validate()
                for err in item_errors:
                    errors.append(f"Item {i+1}: {err}")

        return errors


@dataclass
class OrderResponseDTO:
    """
    DTO for order API responses.
    Shows what the client sees after placing an order.
    """

    order_id: str
    customer_name: str
    customer_email: str
    items: list[dict]
    total: float
    status: str
    item_count: int
    created_at: str

    @classmethod
    def from_model(cls, order: Any) -> "OrderResponseDTO":
        """Convert Order domain model to response DTO."""
        return cls(
            order_id=order.order_id,
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            items=[
                {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.get_subtotal(),
                }
                for item in order.items
            ],
            total=order.get_total(),
            status=order.status,
            item_count=order.get_item_count(),
            created_at=order.created_at.isoformat(),
        )

    def to_dict(self) -> dict:
        """Convert this object into another representation."""
        return {
            "order_id": self.order_id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "items": self.items,
            "total": self.total,
            "status": self.status,
            "item_count": self.item_count,
            "created_at": self.created_at,
        }
