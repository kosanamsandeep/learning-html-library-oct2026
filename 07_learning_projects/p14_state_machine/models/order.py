"""
Order Models - Domain entities for the e-commerce order workflow.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PaymentMethod(Enum):
    """Represents PaymentMethod in this learning project."""
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    COD = "cash_on_delivery"


@dataclass
class OrderItem:
    """Represents OrderItem in this learning project."""
    product_name: str
    quantity: int
    unit_price: float

    @property
    def total(self) -> float:
        """Perform the total step used by this project."""
        return self.quantity * self.unit_price


@dataclass
class Order:
    """Represents Order in this learning project."""
    order_id: str
    customer_name: str
    items: list[OrderItem] = field(default_factory=list)
    payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD
    shipping_address: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: list[str] = field(default_factory=list)

    @property
    def total_amount(self) -> float:
        """Perform the total amount step used by this project."""
        return sum(item.total for item in self.items)

    def add_note(self, note: str) -> None:
        """Add a new item to the in-memory collection, repository, or workflow."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.notes.append(f"[{timestamp}] {note}")
