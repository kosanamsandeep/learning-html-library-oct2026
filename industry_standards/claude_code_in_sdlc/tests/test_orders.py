"""Starting tests for ``src/orders.py``.

The Claude Code skill ``pytest-tdd`` will follow this style: AAA layout,
``parametrize`` over loops, integer cents.
"""

from __future__ import annotations

import pytest

from src.orders import LineItem, compute_total, lookup_price_cents


def test_empty_cart_totals_zero() -> None:
    # Arrange / Act
    total = compute_total([])

    # Assert
    assert total == 0


def test_single_item_total_matches_unit_price() -> None:
    # Arrange
    cart = [LineItem(sku="MUG", quantity=1)]

    # Act
    total = compute_total(cart)

    # Assert
    assert total == lookup_price_cents("MUG")


@pytest.mark.parametrize(
    ("sku", "quantity", "expected"),
    [
        ("MUG", 2, 1998),
        ("BOOK_STD", 3, 4497),
        ("BOOK_HC", 1, 2499),
    ],
)
def test_quantity_multiplies_unit_price(sku: str, quantity: int, expected: int) -> None:
    cart = [LineItem(sku=sku, quantity=quantity)]
    assert compute_total(cart) == expected


def test_welcome10_discount_applies_ten_percent() -> None:
    # Arrange — subtotal of 1000 cents, expect 900 after WELCOME10
    cart = [LineItem(sku="MUG", quantity=1)]  # 999 cents
    expected = (999 * 90) // 100  # = 899

    # Act
    total = compute_total(cart, discount_code="WELCOME10")

    # Assert
    assert total == expected


def test_unknown_discount_raises() -> None:
    cart = [LineItem(sku="MUG", quantity=1)]
    with pytest.raises(ValueError):
        compute_total(cart, discount_code="MYSTERY")
