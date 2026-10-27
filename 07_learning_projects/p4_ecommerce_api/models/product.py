"""
=============================================================================
PROJECT 4: E-COMMERCE API
=============================================================================
FILE: models/product.py
PURPOSE: Product domain model - the internal representation

WHAT YOU LEARN HERE:
- Domain models represent the INTERNAL truth of your system
- They contain business logic and validation
- They are NOT sent directly to the outside world (that's DTOs job!)
=============================================================================
"""


class Product:
    """
    Internal product domain object.

    WHY NOT SEND THIS DIRECTLY TO THE API?
    - It might have internal fields clients shouldn't see (e.g., cost_price)
    - It might have complex objects that don't serialize well
    - Changing this class would break all API clients
    - DTO is the "contract" with the outside world; model is the "truth" inside
    """

    def __init__(
        self,
        product_id: str,
        name: str,
        description: str,
        price: float,
        cost_price: float,  # INTERNAL: clients should NOT see this
        stock_quantity: int,
        category: str,
    ) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self.product_id = product_id
        self.name = name
        self.description = description
        self.price = price
        self.cost_price = cost_price  # Secret! Not in DTO
        self.stock_quantity = stock_quantity
        self.category = category
        self.is_active: bool = True

    def get_profit_margin(self) -> float:
        """Internal business calculation - NOT exposed to clients."""
        if self.cost_price == 0:
            return 0.0
        return ((self.price - self.cost_price) / self.cost_price) * 100

    def is_in_stock(self) -> bool:
        """Return True when the checked condition is satisfied."""
        return self.stock_quantity > 0

    def reduce_stock(self, quantity: int) -> bool:
        """Perform the reduce stock step used by this project."""
        if quantity > self.stock_quantity:
            return False
        self.stock_quantity -= quantity
        return True
