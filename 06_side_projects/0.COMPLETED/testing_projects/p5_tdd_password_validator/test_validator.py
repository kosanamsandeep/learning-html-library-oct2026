"""Tests written first, in the same order as the README narrates the TDD cycle."""

import pytest

from validator import MIN_LENGTH, validate_password


# Step 1: length rule
def test_short_password_is_rejected():
    result = validate_password("Ab1!")
    assert result.ok is False
    assert any("at least 8" in e for e in result.errors)


# Step 2: must contain uppercase
def test_password_without_uppercase_is_rejected():
    result = validate_password("abcdefg1!")
    assert result.ok is False
    assert any("uppercase" in e for e in result.errors)


# Step 3: must contain a digit
def test_password_without_digit_is_rejected():
    result = validate_password("Abcdefgh!")
    assert result.ok is False
    assert any("digit" in e for e in result.errors)


# Step 4: must contain a special character
def test_password_without_special_is_rejected():
    result = validate_password("Abcdefg1")
    assert result.ok is False
    assert any("special" in e for e in result.errors)


# Step 5: no spaces allowed
def test_password_with_space_is_rejected():
    result = validate_password("Abcd efg1!")
    assert result.ok is False
    assert any("space" in e for e in result.errors)


# Step 6: happy path
def test_strong_password_is_accepted():
    result = validate_password("Strong1!")
    assert result.ok is True
    assert result.errors == []


# Step 7: multiple problems are reported together
def test_all_failures_are_collected_at_once():
    result = validate_password("short")
    # short, no uppercase, no digit, no special
    assert result.ok is False
    assert len(result.errors) >= 4


# Parametrized boundary tests
@pytest.mark.parametrize("length", [MIN_LENGTH, MIN_LENGTH + 1, 64])
def test_acceptable_lengths_pass(length):
    # Build a password that satisfies every other rule but varies in length
    base = "Aa1!"
    filler_len = length - len(base)
    password = base + ("x" * filler_len)
    assert len(password) == length
    assert validate_password(password).ok is True


@pytest.mark.parametrize("length", [0, 1, MIN_LENGTH - 1])
def test_too_short_lengths_fail(length):
    password = ("A1!" + "x" * length)[:length]
    assert validate_password(password).ok is False
