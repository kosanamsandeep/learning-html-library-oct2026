"""Example-based tests AND property-based tests, side by side."""

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from math_utils import base64_round_trip, merge_sorted, reverse, safe_average

# ===========================================================================
# Example-based tests (one input, one expected output)
# ===========================================================================


def test_reverse_known_string():
    assert reverse("hello") == "olleh"


def test_merge_sorted_known():
    assert merge_sorted([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]


def test_average_known():
    assert safe_average([2, 4, 6]) == 4


# ===========================================================================
# Property-based tests (hypothesis generates inputs)
# ===========================================================================


@given(st.text())
def test_reverse_is_an_involution(s):
    """Reversing twice always returns the original string."""
    assert reverse(reverse(s)) == s


@given(st.text())
def test_reverse_preserves_length(s):
    assert len(reverse(s)) == len(s)


@given(st.binary())
def test_base64_round_trip_is_lossless(data):
    assert base64_round_trip(data) == data


@given(
    st.lists(st.integers(), max_size=50),
    st.lists(st.integers(), max_size=50),
)
def test_merge_sorted_output_is_sorted(a, b):
    a_sorted = sorted(a)
    b_sorted = sorted(b)
    merged = merge_sorted(a_sorted, b_sorted)
    assert merged == sorted(merged)


@given(
    st.lists(st.integers(), max_size=50),
    st.lists(st.integers(), max_size=50),
)
def test_merge_sorted_preserves_all_elements(a, b):
    a_sorted = sorted(a)
    b_sorted = sorted(b)
    merged = merge_sorted(a_sorted, b_sorted)
    # Multiset equality: same counts of every element.
    assert sorted(merged) == sorted(a_sorted + b_sorted)


# ---------------------------------------------------------------------------
# Property that catches a subtle bug — but we have written the code correctly.
# Hypothesis still helps: it tries empty lists, lists with one element,
# very large numbers, and negative numbers automatically.
# ---------------------------------------------------------------------------


@given(
    st.lists(
        st.floats(allow_nan=False, allow_infinity=False, width=32),
        min_size=1,
        max_size=50,
    )
)
@settings(max_examples=200)
def test_average_is_between_min_and_max(values):
    avg = safe_average(values)
    assert min(values) - 1e-6 <= avg <= max(values) + 1e-6


def test_average_of_empty_list_is_none():
    assert safe_average([]) is None
