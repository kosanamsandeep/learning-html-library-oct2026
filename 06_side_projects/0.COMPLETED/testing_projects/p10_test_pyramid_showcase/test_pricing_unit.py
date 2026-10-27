"""Bottom of the pyramid: many fast unit tests of pure logic."""

import pytest

from pricing import apply_discount, grand_total, shipping_cost


@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (100, 0, 100.00),
        (100, 10, 90.00),
        (100, 50, 50.00),
        (100, 100, 0.00),
        (49.99, 10, 44.99),
    ],
)
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == expected


@pytest.mark.parametrize("bad", [-1, 101, 200])
def test_apply_discount_rejects_out_of_range(bad):
    with pytest.raises(ValueError):
        apply_discount(100, bad)


@pytest.mark.parametrize(
    "total,expected_shipping",
    [
        (0, 5.0),
        (10, 5.0),
        (49.99, 5.0),
        (50, 0.0),
        (200, 0.0),
    ],
)
def test_shipping_cost_threshold(total, expected_shipping):
    assert shipping_cost(total) == expected_shipping


@pytest.mark.parametrize(
    "subtotal,percent,expected_total",
    [
        (60, 0, 60.00),  # no discount, free shipping
        (40, 0, 45.00),  # no discount, shipping applies
        (60, 50, 35.00),  # discounted to 30, plus shipping
        (100, 10, 90.00),  # discounted to 90, free shipping
    ],
)
def test_grand_total(subtotal, percent, expected_total):
    assert grand_total(subtotal, percent) == expected_total
