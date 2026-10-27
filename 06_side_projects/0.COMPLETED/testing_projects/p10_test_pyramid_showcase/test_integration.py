"""Integration tests: real SQLite, plus the service running on top of it."""

import pytest

from service import OutOfStockError


def test_repository_round_trip(repo):
    saved = repo.add("Pen", 5.0, 100)
    fetched = repo.get(saved.id)
    assert fetched == saved


def test_decrement_stock_reduces_count(repo):
    saved = repo.add("Pen", 5.0, 10)
    assert repo.decrement_stock(saved.id, 4) is True
    assert repo.get(saved.id).stock == 6


def test_decrement_stock_refuses_negative_balance(repo):
    saved = repo.add("Pen", 5.0, 2)
    assert repo.decrement_stock(saved.id, 5) is False
    assert repo.get(saved.id).stock == 2  # unchanged


def test_service_against_real_db(service, repo):
    pen = repo.add("Pen", 5.0, 10)
    pad = repo.add("Pad", 25.0, 2)

    result = service.checkout([(pen.id, 4), (pad.id, 1)])

    assert result.subtotal == 45.00
    assert repo.get(pen.id).stock == 6
    assert repo.get(pad.id).stock == 1


def test_service_rolls_back_intent_when_stock_changes(service, repo):
    """Concurrency-style sanity check: if stock disappears between validation
    and reservation, the operation fails cleanly."""
    pen = repo.add("Pen", 5.0, 10)

    # Simulate someone else buying everything mid-checkout
    repo.decrement_stock(pen.id, 10)

    with pytest.raises(OutOfStockError):
        service.checkout([(pen.id, 1)])
