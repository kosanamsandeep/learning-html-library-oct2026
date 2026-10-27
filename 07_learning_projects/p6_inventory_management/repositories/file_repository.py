"""
=============================================================================
PROJECT 6: INVENTORY MANAGEMENT SYSTEM
=============================================================================
FILE: repositories/file_repository.py
PURPOSE: FILE-BASED implementation - same interface, different storage!

THIS PROVES THE REPOSITORY PATTERN:
- Same service code works with MemoryRepository OR FileRepository
- Just swap the implementation - zero code changes in business logic
- This is the power of programming to an interface
=============================================================================
"""

import json
import os
from datetime import datetime
from models.inventory_item import InventoryItem
from .base_repository import BaseInventoryRepository


class FileInventoryRepository(BaseInventoryRepository):
    """
    File-based implementation - persists data to a JSON file.

    SAME INTERFACE as MemoryRepository!
    The service doesn't know (or care) which one it's using.

    TRADE-OFFS vs Memory:
    + Data survives program restart
    + Can be shared between processes
    - Slower (disk I/O)
    - Need to handle file locking (simplified here)
    """

    def __init__(self, file_path: str = "inventory_data.json") -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self._file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create the file if it doesn't exist."""
        if not os.path.exists(self._file_path):
            self._save_data([])

    def _load_data(self) -> list[dict]:
        """Load all items from file."""
        with open(self._file_path, "r") as f:
            return json.load(f)

    def _save_data(self, data: list[dict]) -> None:
        """Save all items to file."""
        with open(self._file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _dict_to_item(self, data: dict) -> InventoryItem:
        """Convert dictionary to InventoryItem."""
        return InventoryItem(
            item_id=data["item_id"],
            name=data["name"],
            sku=data["sku"],
            quantity=data["quantity"],
            min_quantity=data["min_quantity"],
            unit_price=data["unit_price"],
            category=data["category"],
            location=data["location"],
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now().isoformat())
            ),
            updated_at=datetime.fromisoformat(
                data.get("updated_at", datetime.now().isoformat())
            ),
        )

    def _item_to_dict(self, item: InventoryItem) -> dict:
        """Convert InventoryItem to dictionary for storage."""
        return {
            "item_id": item.item_id,
            "name": item.name,
            "sku": item.sku,
            "quantity": item.quantity,
            "min_quantity": item.min_quantity,
            "unit_price": item.unit_price,
            "category": item.category,
            "location": item.location,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        }

    def add(self, item: InventoryItem) -> InventoryItem:
        """Perform the add step used by this project."""
        data = self._load_data()

        # Check for duplicates
        if any(d["item_id"] == item.item_id for d in data):
            raise ValueError(f"Item {item.item_id} already exists")
        if any(d["sku"] == item.sku for d in data):
            raise ValueError(f"SKU {item.sku} already exists")

        data.append(self._item_to_dict(item))
        self._save_data(data)
        return item

    def get_by_id(self, item_id: str) -> InventoryItem | None:
        """Return the requested item or information if it exists."""
        data = self._load_data()
        for d in data:
            if d["item_id"] == item_id:
                return self._dict_to_item(d)
        return None

    def get_by_sku(self, sku: str) -> InventoryItem | None:
        """Return the requested item or information if it exists."""
        data = self._load_data()
        for d in data:
            if d["sku"] == sku:
                return self._dict_to_item(d)
        return None

    def get_all(self) -> list[InventoryItem]:
        """Return the requested item or information if it exists."""
        return [self._dict_to_item(d) for d in self._load_data()]

    def update(self, item: InventoryItem) -> InventoryItem | None:
        """Perform the update step used by this project."""
        data = self._load_data()
        for i, d in enumerate(data):
            if d["item_id"] == item.item_id:
                data[i] = self._item_to_dict(item)
                self._save_data(data)
                return item
        return None

    def delete(self, item_id: str) -> bool:
        """Perform the delete step used by this project."""
        data = self._load_data()
        new_data = [d for d in data if d["item_id"] != item_id]
        if len(new_data) == len(data):
            return False
        self._save_data(new_data)
        return True

    def find_by_category(self, category: str) -> list[InventoryItem]:
        """Search for matching data and return the best result or results."""
        return [
            item for item in self.get_all() if item.category.lower() == category.lower()
        ]

    def find_low_stock(self) -> list[InventoryItem]:
        """Search for matching data and return the best result or results."""
        return [item for item in self.get_all() if item.is_low_stock()]
