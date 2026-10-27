"""
=============================================================================
PROJECT 4: E-COMMERCE API
=============================================================================
FILE: dtos/product_dto.py
PURPOSE: Data Transfer Objects for Product - the "courier boxes"

WHAT YOU LEARN HERE:
- DTO = Data Transfer Object = the package you send to/receive from the outside
- DTOs are SEPARATE from domain models
- They define the CONTRACT between your system and the outside world
- They handle VALIDATION of incoming data
- They control WHAT gets exposed to clients

THE COURIER BOX ANALOGY:
- Domain Model = the actual product in your warehouse (full details, internal pricing)
- DTO = the shipping box (only what the customer needs to see)
- You wouldn't send your entire warehouse inventory sheet to a customer!

WHY SEPARATE DTOs FROM MODELS?
1. Security: Don't expose internal fields (cost_price, profit_margin)
2. Stability: Change internal model without breaking API clients
3. Validation: Validate incoming data BEFORE it touches your domain
4. Transformation: Convert between different representations
=============================================================================
"""

from dataclasses import dataclass, field
from typing import Any

# =============================================================================
# REQUEST DTOs - What clients SEND to us (input validation)
# =============================================================================


@dataclass
class CreateProductDTO:
    """
    DTO for creating a new product.

    THIS IS WHAT THE CLIENT SENDS:
    - Only the fields needed to create a product
    - NO product_id (server generates that)
    - NO cost_price (that's internal)
    - VALIDATION rules defined here

    DATACLASS EXPLAINED:
    - @dataclass auto-generates __init__, __repr__, __eq__
    - Less boilerplate than writing them manually
    - Perfect for DTOs (mostly data, little behavior)
    """

    name: str
    description: str
    price: float
    stock_quantity: int
    category: str

    def validate(self) -> list[str]:
        """
        Validate the DTO data.

        WHY VALIDATE IN THE DTO?
        - Catch bad data at the BOUNDARY (entrance to system)
        - Don't let invalid data reach domain models
        - Return ALL errors at once (not one at a time)

        Returns list of error messages (empty = valid).
        """
        errors: list[str] = []

        if not self.name or not self.name.strip():
            errors.append("Product name is required")
        elif len(self.name) > 200:
            errors.append("Product name must be under 200 characters")

        if self.price <= 0:
            errors.append("Price must be greater than 0")
        elif self.price > 1_000_000:
            errors.append("Price exceeds maximum allowed")

        if self.stock_quantity < 0:
            errors.append("Stock quantity cannot be negative")

        if not self.category or not self.category.strip():
            errors.append("Category is required")

        return errors


@dataclass
class UpdateProductDTO:
    """
    DTO for updating a product.

    NOTE: Fields are Optional (None = don't change).
    This is called a PARTIAL UPDATE or PATCH pattern.
    """

    name: str | None = None
    description: str | None = None
    price: float | None = None
    stock_quantity: int | None = None
    category: str | None = None

    def validate(self) -> list[str]:
        """Validate only the fields that are provided."""
        errors: list[str] = []

        if self.name is not None and not self.name.strip():
            errors.append("Product name cannot be empty")

        if self.price is not None and self.price <= 0:
            errors.append("Price must be greater than 0")

        if self.stock_quantity is not None and self.stock_quantity < 0:
            errors.append("Stock quantity cannot be negative")

        return errors


# =============================================================================
# RESPONSE DTOs - What we SEND BACK to clients (controlled exposure)
# =============================================================================


@dataclass
class ProductResponseDTO:
    """
    DTO for product API responses.

    NOTICE WHAT'S MISSING:
    - No cost_price (internal secret!)
    - No profit_margin (business intelligence, not for customers!)

    NOTICE WHAT'S ADDED:
    - in_stock: computed field for client convenience
    - This is a VIEW of the data, optimized for the API consumer
    """

    product_id: str
    name: str
    description: str
    price: float
    stock_quantity: int
    category: str
    is_active: bool
    in_stock: bool  # Computed field! Not stored in model directly

    @classmethod
    def from_model(cls, product: Any) -> "ProductResponseDTO":
        """
        FACTORY METHOD: Convert domain model → response DTO.

        WHY A FACTORY METHOD?
        - Centralizes the conversion logic
        - If model changes, fix it in ONE place
        - Encapsulates the mapping rules

        Usage: dto = ProductResponseDTO.from_model(product)
        """
        return cls(
            product_id=product.product_id,
            name=product.name,
            description=product.description,
            price=product.price,
            stock_quantity=product.stock_quantity,
            category=product.category,
            is_active=product.is_active,
            in_stock=product.is_in_stock(),  # Computed!
        )

    def to_dict(self) -> dict:
        """Convert to dictionary (for JSON serialization)."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock_quantity": self.stock_quantity,
            "category": self.category,
            "is_active": self.is_active,
            "in_stock": self.in_stock,
        }


@dataclass
class ProductListResponseDTO:
    """Response DTO for listing multiple products."""

    products: list[ProductResponseDTO]
    total_count: int
    page: int = 1
    page_size: int = 20

    def to_dict(self) -> dict:
        """Convert this object into another representation."""
        return {
            "products": [p.to_dict() for p in self.products],
            "total_count": self.total_count,
            "page": self.page,
            "page_size": self.page_size,
        }
