"""
=============================================================================
PROJECT 6: INVENTORY MANAGEMENT SYSTEM
=============================================================================
FILE: models/inventory_item.py
PURPOSE: Domain model for inventory items
=============================================================================
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InventoryItem:
    """
    Represents a single item in inventory.

    NOTE: This model knows NOTHING about WHERE it's stored.
    It could be in memory, a file, a database, or the cloud.
    That's the Repository Pattern's power!
    """

    item_id: str
    name: str
    sku: str  # Stock Keeping Unit (unique barcode)
    quantity: int
    min_quantity: int  # Reorder threshold
    unit_price: float
    category: str
    location: str  # Warehouse location (e.g., "Aisle 3, Shelf B")
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_low_stock(self) -> bool:
        """Check if item needs reordering."""
        return self.quantity <= self.min_quantity

    def is_out_of_stock(self) -> bool:
        """Return True when the checked condition is satisfied."""
        return self.quantity == 0

    def adjust_quantity(self, change: int) -> bool:
        """Adjust quantity (positive=add, negative=remove)."""
        new_quantity = self.quantity + change
        if new_quantity < 0:
            return False
        self.quantity = new_quantity
        self.updated_at = datetime.now()
        return True

    def get_total_value(self) -> float:
        """Calculate total value of this item's stock."""
        return self.quantity * self.unit_price
