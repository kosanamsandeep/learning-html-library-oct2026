"""Pure pricing rules. Unit-test these directly."""

from __future__ import annotations


def apply_discount(price: float, percent: float) -> float:
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return round(price * (1 - percent / 100), 2)


def shipping_cost(total: float) -> float:
    """Free shipping over 50, otherwise flat 5."""
    return 0.0 if total >= 50 else 5.0


def grand_total(subtotal: float, discount_percent: float) -> float:
    discounted = apply_discount(subtotal, discount_percent)
    return round(discounted + shipping_cost(discounted), 2)
