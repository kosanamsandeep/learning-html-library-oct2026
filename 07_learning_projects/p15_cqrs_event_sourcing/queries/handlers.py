"""
Query Handlers - The READ side of CQRS.

Queries read from projections (not from the event store directly).
This separation allows read models to be:
  - Denormalized (fast reads)
  - Multiple (different views of same data)
  - Independently scalable
  - Rebuilt at any time
"""

from __future__ import annotations
from dataclasses import dataclass
from projections.read_models import (
    BalanceProjection,
    TransactionHistoryProjection,
    DailySummaryProjection,
    AccountBalanceView,
    TransactionRecord,
    DailySummary,
)

# ─── Query DTOs ──────────────────────────────────────────────────


@dataclass
class GetBalanceQuery:
    """Represents a read-only request for information."""
    account_id: str


@dataclass
class GetTransactionHistoryQuery:
    """Represents a read-only request for information."""
    account_id: str
    limit: int = 10


@dataclass
class GetAllAccountsQuery:
    """Represents a read-only request for information."""
    pass


@dataclass
class GetDailySummaryQuery:
    """Represents a read-only request for information."""
    date: str


# ─── Query Handler ────────────────────────────────────────────────


class BankQueryHandler:
    """
    Handles read queries by consulting projections.
    Never touches the event store directly.
    """

    def __init__(
        self,
        balance_projection: BalanceProjection,
        history_projection: TransactionHistoryProjection,
        daily_projection: DailySummaryProjection,
    ):
        """Initialize the object with the dependencies or starting values it needs."""
        self._balances = balance_projection
        self._history = history_projection
        self._daily = daily_projection

    def get_balance(self, query: GetBalanceQuery) -> AccountBalanceView | None:
        """Return the requested item or information if it exists."""
        return self._balances.get_balance(query.account_id)

    def get_all_accounts(self, query: GetAllAccountsQuery) -> list[AccountBalanceView]:
        """Return the requested item or information if it exists."""
        return self._balances.get_all_accounts()

    def get_history(self, query: GetTransactionHistoryQuery) -> list[TransactionRecord]:
        """Return the requested item or information if it exists."""
        return self._history.get_history(query.account_id, query.limit)

    def get_daily_summary(self, query: GetDailySummaryQuery) -> DailySummary | None:
        """Return the requested item or information if it exists."""
        return self._daily.get_summary(query.date)

    def get_all_summaries(self) -> list[DailySummary]:
        """Return the requested item or information if it exists."""
        return self._daily.get_all_summaries()
