"""
PROJECT 4: E-COMMERCE API - main.py demo
Demonstrates DTOs as the boundary between outside world and internal models.
"""

from dtos.product_dto import CreateProductDTO, UpdateProductDTO
from dtos.order_dto import CreateOrderDTO, OrderItemDTO
from services.product_service import ProductService


def main() -> None:
    """Perform the main step used by this project."""
    print("=" * 60)
    print("     E-COMMERCE API - DTO Pattern Demo")
    print("=" * 60)

    service = ProductService()

    # =========================================================================
    # Creating products through DTOs (simulating API input)
    # =========================================================================
    print("\n📦 Creating products via DTOs...")

    # This simulates what an API endpoint would receive from a client
    dto1 = CreateProductDTO(
        name="Wireless Headphones",
        description="Noise-canceling bluetooth headphones",
        price=149.99,
        stock_quantity=50,
        category="Electronics",
    )

    dto2 = CreateProductDTO(
        name="Python Textbook",
        description="Advanced Python programming guide",
        price=49.99,
        stock_quantity=100,
        category="Books",
    )

    # Create products (DTOs are validated, converted to models, returned as response DTOs)
    resp1 = service.create_product(dto1)
    resp2 = service.create_product(dto2)

    print(f"  Created: {resp1.name} (ID: {resp1.product_id})")
    print(f"  Created: {resp2.name} (ID: {resp2.product_id})")

    # =========================================================================
    # Show what the client SEES vs what's INTERNAL
    # =========================================================================
    print("\n🔒 What client sees (Response DTO):")
    print(f"  {resp1.to_dict()}")
    print("\n  ⚠️  Notice: NO cost_price or profit_margin exposed!")

    # =========================================================================
    # Validation demo
    # =========================================================================
    print("\n❌ Validation Demo (invalid DTO):")
    bad_dto = CreateProductDTO(
        name="",  # Empty name!
        description="test",
        price=-10,  # Negative price!
        stock_quantity=-5,  # Negative stock!
        category="",  # Empty category!
    )
    errors = bad_dto.validate()
    print(f"  Errors found: {len(errors)}")
    for err in errors:
        print(f"    - {err}")

    # =========================================================================
    # Partial update via DTO
    # =========================================================================
    print("\n✏️  Partial Update (only change price):")
    update_dto = UpdateProductDTO(price=129.99)  # Only update price!
    updated = service.update_product(resp1.product_id, update_dto)
    print(f"  Before: $149.99 → After: ${updated.price}")
    print(f"  Name unchanged: {updated.name}")

    # =========================================================================
    # List with pagination
    # =========================================================================
    print("\n📋 Product Listing (paginated response):")
    listing = service.list_products(page=1, page_size=10)
    print(f"  Total products: {listing.total_count}")
    print(f"  Page {listing.page} of size {listing.page_size}")
    for p in listing.products:
        stock_status = "✅ In Stock" if p.in_stock else "❌ Out of Stock"
        print(f"    {p.name} - ${p.price:.2f} [{stock_status}]")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
