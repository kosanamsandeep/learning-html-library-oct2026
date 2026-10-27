"""A small shopping cart used to teach fixtures and parametrize in P2."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Product:
    sku: str
    name: str
    price: float


@dataclass
class ShoppingCart:
    items: dict[str, int] = field(default_factory=dict)  # sku -> quantity
    catalog: dict[str, Product] = field(default_factory=dict)

    def add(self, sku: str, quantity: int = 1) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if sku not in self.catalog:
            raise KeyError(f"unknown product: {sku}")
        self.items[sku] = self.items.get(sku, 0) + quantity

    def remove(self, sku: str) -> None:
        self.items.pop(sku, None)

    def total(self) -> float:
        return round(
            sum(self.catalog[sku].price * qty for sku, qty in self.items.items()),
            2,
        )

    def line_count(self) -> int:
        return len(self.items)

    def apply_discount(self, percent: float) -> float:
        if not 0 <= percent <= 100:
            raise ValueError("percent must be between 0 and 100")
        return round(self.total() * (1 - percent / 100), 2)
