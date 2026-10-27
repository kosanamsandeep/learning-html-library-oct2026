"""Toy order-management module used by the Claude Code SDLC sample.

The point of this file is *not* to be a complete domain model. It is a small
playground the agent can iterate on while following the conventions in
``CLAUDE.md`` and the ``pytest-tdd`` skill.

Conventions that apply here:

* Money is stored as **integer cents** — never floats.
* Public functions have type hints.
* No third-party dependencies; pure stdlib.
"""

from __future__ import annotations

from dataclasses import dataclass

# Frozen so legacy pricing tables stay immutable. The pricing team owns
# this constant — `CLAUDE.md` explicitly tells the agent not to touch it.
LEGACY_PRICE_RULES: dict[str, int] = {
    "BOOK_STD": 1499,
    "BOOK_HC": 2499,
    "MUG": 999,
}


@dataclass(frozen=True)
class LineItem:
    """A single line in a cart: a product code and a quantity."""

    sku: str
    quantity: int


def lookup_price_cents(sku: str) -> int:
    """Return the unit price for ``sku`` in integer cents.

    Raises ``KeyError`` if the SKU is not in the legacy price table — that
    is the contract the rest of the codebase relies on, so don't soften it.
    """
    return LEGACY_PRICE_RULES[sku]


def compute_total(items: list[LineItem], discount_code: str | None = None) -> int:
    """Compute the grand total for ``items`` in cents, applying ``discount_code``.

    Discount semantics:
    * ``None`` (or empty string) — no discount.
    * ``"WELCOME10"`` — 10% off the subtotal, rounded down to whole cents.
    * Any other value raises ``ValueError``.

    The function does *not* validate quantity > 0 — that is the caller's job.
    """
    subtotal = sum(lookup_price_cents(item.sku) * item.quantity for item in items)

    if not discount_code:
        return subtotal
    if discount_code == "WELCOME10":
        return (subtotal * 90) // 100
    raise ValueError(f"unknown discount code: {discount_code!r}")
