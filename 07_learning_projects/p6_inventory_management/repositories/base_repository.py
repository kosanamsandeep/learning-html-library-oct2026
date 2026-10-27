"""
=============================================================================
PROJECT 6: INVENTORY MANAGEMENT SYSTEM
=============================================================================
FILE: repositories/base_repository.py
PURPOSE: Define the ABSTRACT repository interface (contract)

WHAT YOU LEARN HERE:
- REPOSITORY PATTERN: Separates business logic from data persistence
- ABSTRACT CLASS: Defines WHAT a repository must do, not HOW
- Any implementation (memory, file, database) must follow this contract

THE WAREHOUSE CLERK ANALOGY:
- Service says: "Give me item SKU-123"
- Repository (the clerk) knows WHERE to find it
- Service doesn't care if clerk looks in a filing cabinet, computer, or warehouse

WHY THIS PATTERN?
- Want to switch from in-memory to PostgreSQL? Just write a new repository!
- Want to test without a real database? Use the in-memory repository!
- Service code NEVER changes when storage changes
- This is DEPENDENCY INVERSION PRINCIPLE (DIP) in action
=============================================================================
"""

from abc import ABC, abstractmethod
from models.inventory_item import InventoryItem


class BaseInventoryRepository(ABC):
    """
    ABSTRACT repository interface.

    THIS IS A CONTRACT:
    - Defines the methods ANY repository implementation MUST provide
    - Cannot be instantiated directly (it's abstract)
    - Forces all implementations to have the same interface

    THINK OF IT AS:
    - "Any warehouse clerk must be able to: find items, add items, remove items, list items"
    - HOW they do it is up to them (filing cabinet, computer, shouting across the room)
    """

    @abstractmethod
    def add(self, item: InventoryItem) -> InventoryItem:
        """
        Store a new item.

        MUST be implemented by all repositories.
        Whether it's saving to memory, file, or database.
        """
        pass

    @abstractmethod
    def get_by_id(self, item_id: str) -> InventoryItem | None:
        """Find an item by its ID."""
        pass

    @abstractmethod
    def get_by_sku(self, sku: str) -> InventoryItem | None:
        """Find an item by SKU (barcode)."""
        pass

    @abstractmethod
    def get_all(self) -> list[InventoryItem]:
        """Get all items."""
        pass

    @abstractmethod
    def update(self, item: InventoryItem) -> InventoryItem | None:
        """Update an existing item."""
        pass

    @abstractmethod
    def delete(self, item_id: str) -> bool:
        """Delete an item by ID."""
        pass

    @abstractmethod
    def find_by_category(self, category: str) -> list[InventoryItem]:
        """Find all items in a category."""
        pass

    @abstractmethod
    def find_low_stock(self) -> list[InventoryItem]:
        """Find all items below minimum quantity."""
        pass
