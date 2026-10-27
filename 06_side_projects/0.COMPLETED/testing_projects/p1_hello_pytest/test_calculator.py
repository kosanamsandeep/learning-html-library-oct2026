"""First pytest tests. Each test follows Arrange / Act / Assert."""

import pytest

from calculator import add, divide, multiply, subtract


def test_add_two_positive_numbers():
    # Arrange
    a, b = 2, 3
    # Act
    result = add(a, b)
    # Assert
    assert result == 5


def test_subtract_gives_negative_when_b_is_bigger():
    assert subtract(2, 5) == -3


def test_multiply_by_zero_is_zero():
    assert multiply(7, 0) == 0


def test_divide_returns_float_quotient():
    assert divide(10, 4) == 2.5


def test_divide_by_zero_raises():
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)
