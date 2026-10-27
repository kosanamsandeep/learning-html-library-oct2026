"""
=============================================================================
PROJECT 4: E-COMMERCE API
=============================================================================
FILE: services/product_service.py
PURPOSE: Business logic that uses DTOs for input/output

KEY PATTERN:
    Input DTO → Service → Domain Model → Service → Output DTO
    (validate)   (logic)   (internal)     (logic)   (safe output)
=============================================================================
"""

import uuid
from models.product import Product
from dtos.product_dto import (
    CreateProductDTO,
    UpdateProductDTO,
    ProductResponseDTO,
    ProductListResponseDTO,
)


class ProductService:
    """
    Product business operations.

    THE DTO FLOW:
    1. Receive CreateProductDTO (validated input from client)
    2. Create Product domain model (internal representation)
    3. Return ProductResponseDTO (safe output to client)

    The domain model is NEVER exposed directly!
    """

    def __init__(self) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self._products: dict[str, Product] = {}

    def create_product(self, dto: CreateProductDTO) -> ProductResponseDTO:
        """
        Create a product from a DTO.

        FLOW:
        1. Validate DTO (already done by caller, but double-check)
        2. Generate internal fields (ID, cost_price)
        3. Create domain model
        4. Return response DTO (hides internal details)
        """
        # Validate
        errors = dto.validate()
        if errors:
            raise ValueError(f"Validation failed: {', '.join(errors)}")

        # Generate server-side data
        product_id = f"PRD-{uuid.uuid4().hex[:8].upper()}"

        # Create domain model with internal data
        product = Product(
            product_id=product_id,
            name=dto.name.strip(),
            description=dto.description,
            price=dto.price,
            cost_price=dto.price * 0.6,  # Internal: 60% of price is cost
            stock_quantity=dto.stock_quantity,
            category=dto.category.strip(),
        )

        self._products[product_id] = product

        # Return DTO (hides cost_price!)
        return ProductResponseDTO.from_model(product)

    def get_product(self, product_id: str) -> ProductResponseDTO | None:
        """Get a product as a DTO (safe for client consumption)."""
        product = self._products.get(product_id)
        if product is None:
            return None
        return ProductResponseDTO.from_model(product)

    def update_product(
        self, product_id: str, dto: UpdateProductDTO
    ) -> ProductResponseDTO | None:
        """Update product fields from a partial DTO."""
        product = self._products.get(product_id)
        if product is None:
            return None

        errors = dto.validate()
        if errors:
            raise ValueError(f"Validation failed: {', '.join(errors)}")

        # Apply only provided fields (PATCH pattern)
        if dto.name is not None:
            product.name = dto.name.strip()
        if dto.description is not None:
            product.description = dto.description
        if dto.price is not None:
            product.price = dto.price
            product.cost_price = dto.price * 0.6  # Recalculate internal
        if dto.stock_quantity is not None:
            product.stock_quantity = dto.stock_quantity
        if dto.category is not None:
            product.category = dto.category.strip()

        return ProductResponseDTO.from_model(product)

    def list_products(
        self, page: int = 1, page_size: int = 20
    ) -> ProductListResponseDTO:
        """Get paginated list of products."""
        all_products = list(self._products.values())
        total = len(all_products)

        # Pagination
        start = (page - 1) * page_size
        end = start + page_size
        page_products = all_products[start:end]

        return ProductListResponseDTO(
            products=[ProductResponseDTO.from_model(p) for p in page_products],
            total_count=total,
            page=page,
            page_size=page_size,
        )

    def delete_product(self, product_id: str) -> bool:
        """Soft-delete a product (mark inactive)."""
        product = self._products.get(product_id)
        if product is None:
            return False
        product.is_active = False
        return True
