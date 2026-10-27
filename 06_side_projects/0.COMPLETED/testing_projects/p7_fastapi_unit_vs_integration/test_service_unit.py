"""Unit tests: hit ItemService directly. No HTTP, no JSON, no FastAPI."""

import pytest


def test_create_returns_item_with_id(service):
    item = service.create("Pen", 1.50)
    assert item.id == 1
    assert item.name == "Pen"
    assert item.price == 1.50


def test_create_strips_whitespace(service):
    item = service.create("  Pen  ", 1.50)
    assert item.name == "Pen"


def test_create_rounds_price(service):
    item = service.create("Pen", 1.499)
    assert item.price == 1.50


@pytest.mark.parametrize("bad_name", ["", "   "])
def test_create_rejects_empty_name(service, bad_name):
    with pytest.raises(ValueError):
        service.create(bad_name, 1.0)


def test_create_rejects_negative_price(service):
    with pytest.raises(ValueError):
        service.create("Pen", -0.01)


def test_total_value_sums_all_prices(service):
    service.create("a", 1.10)
    service.create("b", 2.20)
    service.create("c", 3.70)
    assert service.total_value() == 7.00
