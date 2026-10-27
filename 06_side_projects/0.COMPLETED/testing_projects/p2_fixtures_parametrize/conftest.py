"""Shared fixtures live in conftest.py and are auto-discovered by pytest."""

import pytest

from cart import Product, ShoppingCart


@pytest.fixture
def catalog() -> dict[str, Product]:
    """A small product catalog used by every cart test."""
    return {
        "A1": Product("A1", "Notebook", 5.00),
        "B2": Product("B2", "Pen", 1.50),
        "C3": Product("C3", "Backpack", 49.99),
    }


@pytest.fixture
def empty_cart(catalog) -> ShoppingCart:
    """A fresh, empty cart wired to the shared catalog."""
    return ShoppingCart(catalog=catalog)


@pytest.fixture
def cart_with_items(empty_cart) -> ShoppingCart:
    """A cart pre-loaded with a few items so tests can focus on behavior."""
    empty_cart.add("A1", 2)  # 2 x 5.00 = 10.00
    empty_cart.add("B2", 4)  # 4 x 1.50 = 6.00
    return empty_cart
