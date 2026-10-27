"""
=============================================================================
PROJECT 6: INVENTORY MANAGEMENT SYSTEM
=============================================================================
FILE: repositories/memory_repository.py
PURPOSE: IN-MEMORY implementation of the repository

THIS IMPLEMENTATION:
- Stores items in a Python dictionary (RAM only)
- Fast, simple, perfect for testing
- Data is LOST when program exits
- Used in development and unit tests

VS OTHER IMPLEMENTATIONS:
- FileRepository: Saves to JSON/CSV (Project 7 might add this)
- DatabaseRepository: Saves to SQLite/PostgreSQL
- CloudRepository: Saves to AWS DynamoDB or similar
- ALL follow the same interface (BaseInventoryRepository)
=============================================================================
"""

from models.inventory_item import InventoryItem
from .base_repository import BaseInventoryRepository


class MemoryInventoryRepository(BaseInventoryRepository):
    """
    In-memory implementation of inventory repository.

    IMPLEMENTS ALL ABSTRACT METHODS from BaseInventoryRepository.
    Python will raise TypeError if we forget to implement any method!

    PERFECT FOR:
    - Unit testing (fast, no external dependencies)
    - Development (no database setup needed)
    - Prototyping (quick iteration)
    """

    def __init__(self) -> None:
        # Simple dictionary storage: item_id → InventoryItem
        """Initialize the object with the dependencies or starting values it needs."""
        self._storage: dict[str, InventoryItem] = {}
        # Secondary index for SKU lookups (faster than scanning all items)
        self._sku_index: dict[str, str] = {}  # sku → item_id

    def add(self, item: InventoryItem) -> InventoryItem:
        """Store item in memory dictionary."""
        if item.item_id in self._storage:
            raise ValueError(f"Item {item.item_id} already exists")
        if item.sku in self._sku_index:
            raise ValueError(f"SKU {item.sku} already exists")

        self._storage[item.item_id] = item
        self._sku_index[item.sku] = item.item_id
        return item

    def get_by_id(self, item_id: str) -> InventoryItem | None:
        """O(1) lookup by ID."""
        return self._storage.get(item_id)

    def get_by_sku(self, sku: str) -> InventoryItem | None:
        """O(1) lookup by SKU using secondary index."""
        item_id = self._sku_index.get(sku)
        if item_id is None:
            return None
        return self._storage.get(item_id)

    def get_all(self) -> list[InventoryItem]:
        """Return all items."""
        return list(self._storage.values())

    def update(self, item: InventoryItem) -> InventoryItem | None:
        """Update existing item in storage."""
        if item.item_id not in self._storage:
            return None
        self._storage[item.item_id] = item
        return item

    def delete(self, item_id: str) -> bool:
        """Remove item from storage."""
        item = self._storage.get(item_id)
        if item is None:
            return False
        del self._storage[item_id]
        del self._sku_index[item.sku]
        return True

    def find_by_category(self, category: str) -> list[InventoryItem]:
        """Filter items by category."""
        return [
            item
            for item in self._storage.values()
            if item.category.lower() == category.lower()
        ]

    def find_low_stock(self) -> list[InventoryItem]:
        """Find items at or below minimum quantity."""
        return [item for item in self._storage.values() if item.is_low_stock()]
