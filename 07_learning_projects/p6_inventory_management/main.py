"""
PROJECT 6: INVENTORY MANAGEMENT - Demo
Shows how the SAME service works with DIFFERENT repositories.
"""

from repositories.memory_repository import MemoryInventoryRepository
from repositories.file_repository import FileInventoryRepository
from services.inventory_service import InventoryService


def run_demo(service: InventoryService, repo_name: str) -> None:
    """Run the same demo with any repository implementation."""
    print(f"\n{'='*60}")
    print(f"  Using: {repo_name}")
    print(f"{'='*60}")

    # Add items
    item1 = service.add_item(
        "Laptop Pro 15", "LAP-001", 25, 10, 1299.99, "Electronics", "Aisle 1, Shelf A"
    )
    item2 = service.add_item(
        "USB-C Cable", "USB-001", 150, 50, 12.99, "Accessories", "Aisle 3, Shelf C"
    )
    item3 = service.add_item(
        "Wireless Mouse", "MOU-001", 8, 15, 29.99, "Accessories", "Aisle 3, Shelf D"
    )  # Low stock!

    print(f"\n  Added: {item1.name} (Qty: {item1.quantity})")
    print(f"  Added: {item2.name} (Qty: {item2.quantity})")
    print(f"  Added: {item3.name} (Qty: {item3.quantity})")

    # Receive stock
    print("\n  📦 Receiving 5 more Wireless Mouse...")
    updated = service.receive_stock(item3.item_id, 5)
    print(f"  New quantity: {updated.quantity}")

    # Ship stock
    print("  🚚 Shipping 3 Laptop Pro 15...")
    updated = service.ship_stock(item1.item_id, 3)
    print(f"  Remaining: {updated.quantity}")

    # Low stock alerts
    print("\n  ⚠️  Low Stock Alerts:")
    alerts = service.get_low_stock_alerts()
    for item in alerts:
        print(f"    {item.name}: {item.quantity}/{item.min_quantity} (min)")

    # Summary
    print("\n  📊 Inventory Summary:")
    summary = service.get_inventory_summary()
    for key, val in summary.items():
        print(f"    {key}: {val}")


def main() -> None:
    """Perform the main step used by this project."""
    print("=" * 60)
    print("   INVENTORY MANAGEMENT - Repository Pattern Demo")
    print("=" * 60)
    print("\n  The SAME service code runs with DIFFERENT storage backends!")
    print("  This is the power of the Repository Pattern + Dependency Injection.")

    # Demo 1: In-memory repository (fast, data lost on exit)
    memory_repo = MemoryInventoryRepository()
    memory_service = InventoryService(memory_repo)
    run_demo(memory_service, "MemoryInventoryRepository (RAM - fast, temporary)")

    # Demo 2: File repository (persistent, slower)
    file_repo = FileInventoryRepository("demo_inventory.json")
    file_service = InventoryService(file_repo)
    run_demo(file_service, "FileInventoryRepository (JSON file - persistent)")

    print("\n\n🔑 KEY INSIGHT:")
    print("  Notice how run_demo() is IDENTICAL for both!")
    print("  The service doesn't know or care about storage.")
    print("  Swap repositories without changing business logic!")

    # Cleanup demo file
    import os

    if os.path.exists("demo_inventory.json"):
        os.remove("demo_inventory.json")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
