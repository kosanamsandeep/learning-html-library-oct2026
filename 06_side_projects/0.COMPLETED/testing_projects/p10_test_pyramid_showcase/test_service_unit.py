"""Unit-test the service in isolation by mocking the repository."""

import pytest

from repository import Product
from service import CheckoutService, OutOfStockError, UnknownProductError


def test_checkout_calculates_subtotal_and_total(fake_repo):
    fake_repo.get.side_effect = lambda pid: {
        1: Product(1, "Pen", 5.00, 100),
        2: Product(2, "Pad", 25.00, 10),
    }[pid]
    fake_repo.decrement_stock.return_value = True

    result = CheckoutService(fake_repo).checkout(
        items=[(1, 4), (2, 1)], discount_percent=10
    )

    assert result.subtotal == 45.00
    # 10% off 45 = 40.50, plus 5 shipping (under 50) = 45.50
    assert result.total == 45.50


def test_checkout_unknown_product_raises(fake_repo):
    fake_repo.get.return_value = None

    with pytest.raises(UnknownProductError):
        CheckoutService(fake_repo).checkout([(1, 1)])


def test_checkout_insufficient_stock_raises(fake_repo):
    fake_repo.get.return_value = Product(1, "Pen", 5.00, stock=2)

    with pytest.raises(OutOfStockError):
        CheckoutService(fake_repo).checkout([(1, 5)])


def test_checkout_does_not_decrement_when_validation_fails(fake_repo):
    fake_repo.get.return_value = Product(1, "Pen", 5.00, stock=0)

    with pytest.raises(OutOfStockError):
        CheckoutService(fake_repo).checkout([(1, 1)])

    fake_repo.decrement_stock.assert_not_called()
