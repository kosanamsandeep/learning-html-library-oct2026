"""
=============================================================================
PROJECT 6: INVENTORY MANAGEMENT SYSTEM
=============================================================================
FILE: services/inventory_service.py
PURPOSE: Business logic that DEPENDS ON the repository INTERFACE

KEY INSIGHT:
- This service accepts a BaseInventoryRepository (the INTERFACE)
- It works with ANY implementation (memory, file, database)
- The service never knows or cares about storage details
- This is DEPENDENCY INJECTION in action
=============================================================================
"""

import uuid
from models.inventory_item import InventoryItem
from repositories.base_repository import BaseInventoryRepository


class InventoryService:
    """
    Business logic for inventory management.

    DEPENDENCY INJECTION:
    - The repository is INJECTED through the constructor
    - We depend on the ABSTRACT interface, not a concrete class
    - This makes the service testable and flexible

    Example:
        # For production:
        repo = FileInventoryRepository("warehouse.json")
        service = InventoryService(repo)

        # For testing:
        repo = MemoryInventoryRepository()
        service = InventoryService(repo)

        # Same service, different storage!
    """

    def __init__(self, repository: BaseInventoryRepository) -> None:
        """
        DEPENDENCY INJECTION: Repository is passed in, not created here.

        WHY NOT just do: self._repo = MemoryInventoryRepository()?
        - That would HARDCODE the dependency
        - Can't switch to file/database without changing this class
        - Can't test without actual storage
        - Violates DEPENDENCY INVERSION PRINCIPLE
        """
        self._repo: BaseInventoryRepository = repository

    def add_item(
        self,
        name: str,
        sku: str,
        quantity: int,
        min_quantity: int,
        unit_price: float,
        category: str,
        location: str,
    ) -> InventoryItem:
        """Add a new inventory item."""
        # Business validation
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if unit_price < 0:
            raise ValueError("Price cannot be negative")
        if not sku.strip():
            raise ValueError("SKU is required")

        # Check for duplicate SKU
        existing = self._repo.get_by_sku(sku)
        if existing:
            raise ValueError(f"SKU '{sku}' already exists")

        item = InventoryItem(
            item_id=f"INV-{uuid.uuid4().hex[:8].upper()}",
            name=name.strip(),
            sku=sku.strip().upper(),
            quantity=quantity,
            min_quantity=min_quantity,
            unit_price=unit_price,
            category=category.strip(),
            location=location.strip(),
        )

        return self._repo.add(item)

    def receive_stock(self, item_id: str, quantity: int) -> InventoryItem | None:
        """Receive new stock (increase quantity)."""
        if quantity <= 0:
            raise ValueError("Receive quantity must be positive")

        item = self._repo.get_by_id(item_id)
        if item is None:
            return None

        item.adjust_quantity(quantity)
        return self._repo.update(item)

    def ship_stock(self, item_id: str, quantity: int) -> InventoryItem | None:
        """Ship stock out (decrease quantity)."""
        if quantity <= 0:
            raise ValueError("Ship quantity must be positive")

        item = self._repo.get_by_id(item_id)
        if item is None:
            return None

        if not item.adjust_quantity(-quantity):
            raise ValueError(f"Insufficient stock. Available: {item.quantity}")

        return self._repo.update(item)

    def get_item(self, item_id: str) -> InventoryItem | None:
        """Return the requested item or information if it exists."""
        return self._repo.get_by_id(item_id)

    def get_item_by_sku(self, sku: str) -> InventoryItem | None:
        """Return the requested item or information if it exists."""
        return self._repo.get_by_sku(sku)

    def get_all_items(self) -> list[InventoryItem]:
        """Return the requested item or information if it exists."""
        return self._repo.get_all()

    def get_low_stock_alerts(self) -> list[InventoryItem]:
        """Get all items that need reordering."""
        return self._repo.find_low_stock()

    def get_category_items(self, category: str) -> list[InventoryItem]:
        """Return the requested item or information if it exists."""
        return self._repo.find_by_category(category)

    def get_inventory_value(self) -> float:
        """Calculate total inventory value."""
        return sum(item.get_total_value() for item in self._repo.get_all())

    def get_inventory_summary(self) -> dict:
        """Generate inventory summary report."""
        items = self._repo.get_all()
        return {
            "total_items": len(items),
            "total_value": sum(i.get_total_value() for i in items),
            "low_stock_count": len(self._repo.find_low_stock()),
            "out_of_stock": len([i for i in items if i.is_out_of_stock()]),
            "categories": list(set(i.category for i in items)),
        }
