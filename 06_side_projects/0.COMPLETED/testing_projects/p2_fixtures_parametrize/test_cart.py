"""Tests that show off fixtures (reusable setup) and parametrize (many inputs)."""

import pytest


def test_empty_cart_has_zero_total(empty_cart):
    assert empty_cart.total() == 0
    assert empty_cart.line_count() == 0


def test_adding_items_updates_total(cart_with_items):
    assert cart_with_items.total() == 16.00
    assert cart_with_items.line_count() == 2


def test_removing_item_drops_it_from_total(cart_with_items):
    cart_with_items.remove("A1")
    assert cart_with_items.total() == 6.00


def test_removing_unknown_sku_is_a_no_op(cart_with_items):
    cart_with_items.remove("ZZZ")
    assert cart_with_items.total() == 16.00


@pytest.mark.parametrize(
    "sku,quantity,expected_total",
    [
        ("A1", 1, 5.00),
        ("A1", 3, 15.00),
        ("B2", 10, 15.00),
        ("C3", 1, 49.99),
    ],
)
def test_total_for_single_product(empty_cart, sku, quantity, expected_total):
    empty_cart.add(sku, quantity)
    assert empty_cart.total() == expected_total


@pytest.mark.parametrize("bad_quantity", [0, -1, -100])
def test_add_rejects_non_positive_quantity(empty_cart, bad_quantity):
    with pytest.raises(ValueError):
        empty_cart.add("A1", bad_quantity)


def test_unknown_product_cannot_be_added(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.add("UNKNOWN")


@pytest.mark.parametrize(
    "percent,expected",
    [
        (0, 16.00),
        (10, 14.40),
        (50, 8.00),
        (100, 0.00),
    ],
)
def test_discount_is_applied_correctly(cart_with_items, percent, expected):
    assert cart_with_items.apply_discount(percent) == expected


@pytest.mark.parametrize("bad_percent", [-1, 101, 150])
def test_invalid_discount_percent_raises(cart_with_items, bad_percent):
    with pytest.raises(ValueError):
        cart_with_items.apply_discount(bad_percent)
