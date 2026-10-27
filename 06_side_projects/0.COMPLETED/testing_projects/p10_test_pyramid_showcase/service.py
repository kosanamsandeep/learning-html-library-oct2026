"""Checkout service. Combines repository + pricing.

This is the layer that benefits most from mocks: we can unit-test the
business rule without touching the database.
"""

from __future__ import annotations

from dataclasses import dataclass

from pricing import grand_total
from repository import ProductRepository


class OutOfStockError(Exception):
    pass


class UnknownProductError(Exception):
    pass


@dataclass
class CheckoutResult:
    subtotal: float
    total: float


class CheckoutService:
    def __init__(self, repo: ProductRepository) -> None:
        self.repo = repo

    def checkout(
        self,
        items: list[tuple[int, int]],  # [(product_id, quantity), ...]
        discount_percent: float = 0.0,
    ) -> CheckoutResult:
        subtotal = 0.0
        for product_id, qty in items:
            product = self.repo.get(product_id)
            if product is None:
                raise UnknownProductError(f"product {product_id} not found")
            if product.stock < qty:
                raise OutOfStockError(f"insufficient stock for {product.name}")
            subtotal += product.price * qty

        # Reserve stock only after every line item is valid
        for product_id, qty in items:
            ok = self.repo.decrement_stock(product_id, qty)
            if not ok:
                raise OutOfStockError(
                    f"stock changed during checkout for product {product_id}"
                )

        subtotal = round(subtotal, 2)
        return CheckoutResult(
            subtotal=subtotal,
            total=grand_total(subtotal, discount_percent),
        )
