"""
Projections - The READ side of CQRS.

Projections build optimized read models from events.
They are DISPOSABLE — can be rebuilt at any time by replaying events.

Key insight: The write model (events) and read model (projections) are different.
You can have MULTIPLE projections from the same events, each optimized for
different query patterns.

Example projections:
  - Account balance (optimized for "what's my balance?")
  - Transaction history (optimized for "show my last 10 transactions")
  - Daily summary (optimized for "what happened today?")
  - Leaderboard (optimized for "who has the most money?")
"""

from __future__ import annotations
from dataclasses import dataclass, field
from events.event_store import DomainEvent

# ─── Projection 1: Account Balance View ──────────────────────────


@dataclass
class AccountBalanceView:
    """Represents AccountBalanceView in this learning project."""
    account_id: str
    owner_name: str
    balance: float
    account_type: str
    is_frozen: bool = False
    is_closed: bool = False
    transaction_count: int = 0


class BalanceProjection:
    """
    Projects events into account balance read model.
    Optimized for: "What is account X's current balance?"
    """

    def __init__(self):
        """Initialize the object with the dependencies or starting values it needs."""
        self._accounts: dict[str, AccountBalanceView] = {}

    def handle_event(self, event: DomainEvent) -> None:
        """Update projection when new event arrives."""
        if event.event_type == "AccountOpened":
            self._accounts[event.aggregate_id] = AccountBalanceView(
                account_id=event.aggregate_id,
                owner_name=event.data.get("owner_name", ""),
                balance=event.data.get("initial_deposit", 0.0),
                account_type=event.data.get("account_type", "checking"),
            )

        elif event.event_type == "MoneyDeposited":
            if event.aggregate_id in self._accounts:
                acct = self._accounts[event.aggregate_id]
                acct.balance += event.data.get("amount", 0.0)
                acct.transaction_count += 1

        elif event.event_type == "MoneyWithdrawn":
            if event.aggregate_id in self._accounts:
                acct = self._accounts[event.aggregate_id]
                acct.balance -= event.data.get("amount", 0.0)
                acct.transaction_count += 1

        elif event.event_type == "TransferInitiated":
            if event.aggregate_id in self._accounts:
                acct = self._accounts[event.aggregate_id]
                acct.balance -= event.data.get("amount", 0.0)
                acct.transaction_count += 1

        elif event.event_type == "TransferCompleted":
            if event.aggregate_id in self._accounts:
                acct = self._accounts[event.aggregate_id]
                acct.balance += event.data.get("amount", 0.0)
                acct.transaction_count += 1

        elif event.event_type == "AccountFrozen":
            if event.aggregate_id in self._accounts:
                self._accounts[event.aggregate_id].is_frozen = True

        elif event.event_type == "AccountClosed":
            if event.aggregate_id in self._accounts:
                self._accounts[event.aggregate_id].is_closed = True

    def get_balance(self, account_id: str) -> AccountBalanceView | None:
        """Return the requested item or information if it exists."""
        return self._accounts.get(account_id)

    def get_all_accounts(self) -> list[AccountBalanceView]:
        """Return the requested item or information if it exists."""
        return list(self._accounts.values())


# ─── Projection 2: Transaction History ───────────────────────────


@dataclass
class TransactionRecord:
    """Represents TransactionRecord in this learning project."""
    timestamp: str
    event_type: str
    account_id: str
    amount: float
    description: str
    balance_after: float = 0.0


class TransactionHistoryProjection:
    """
    Projects events into transaction history.
    Optimized for: "Show me transaction history for account X."
    """

    def __init__(self):
        """Initialize the object with the dependencies or starting values it needs."""
        self._history: dict[str, list[TransactionRecord]] = {}
        self._running_balances: dict[str, float] = {}

    def handle_event(self, event: DomainEvent) -> None:
        """Build transaction records from events."""
        if event.event_type == "AccountOpened":
            self._history[event.aggregate_id] = []
            self._running_balances[event.aggregate_id] = event.data.get(
                "initial_deposit", 0.0
            )
            if event.data.get("initial_deposit", 0) > 0:
                self._add_record(
                    event.aggregate_id,
                    event,
                    event.data["initial_deposit"],
                    "Opening deposit",
                )

        elif event.event_type == "MoneyDeposited":
            amount = event.data.get("amount", 0.0)
            self._running_balances[event.aggregate_id] = (
                self._running_balances.get(event.aggregate_id, 0) + amount
            )
            self._add_record(
                event.aggregate_id,
                event,
                amount,
                event.data.get("description", "Deposit"),
            )

        elif event.event_type == "MoneyWithdrawn":
            amount = event.data.get("amount", 0.0)
            self._running_balances[event.aggregate_id] = (
                self._running_balances.get(event.aggregate_id, 0) - amount
            )
            self._add_record(
                event.aggregate_id,
                event,
                -amount,
                event.data.get("description", "Withdrawal"),
            )

        elif event.event_type == "TransferInitiated":
            amount = event.data.get("amount", 0.0)
            self._running_balances[event.aggregate_id] = (
                self._running_balances.get(event.aggregate_id, 0) - amount
            )
            to_id = event.data.get("to_account_id", "?")
            self._add_record(event.aggregate_id, event, -amount, f"Transfer to {to_id}")

        elif event.event_type == "TransferCompleted":
            amount = event.data.get("amount", 0.0)
            self._running_balances[event.aggregate_id] = (
                self._running_balances.get(event.aggregate_id, 0) + amount
            )
            from_id = event.data.get("from_account_id", "?")
            self._add_record(
                event.aggregate_id, event, amount, f"Transfer from {from_id}"
            )

    def _add_record(
        self, account_id: str, event: DomainEvent, amount: float, desc: str
    ) -> None:
        """Perform the add record step used by this project."""
        if account_id not in self._history:
            self._history[account_id] = []
        self._history[account_id].append(
            TransactionRecord(
                timestamp=event.timestamp,
                event_type=event.event_type,
                account_id=account_id,
                amount=amount,
                description=desc,
                balance_after=self._running_balances.get(account_id, 0.0),
            )
        )

    def get_history(self, account_id: str, limit: int = 10) -> list[TransactionRecord]:
        """Return the requested item or information if it exists."""
        records = self._history.get(account_id, [])
        return records[-limit:]

    def get_all_transactions(self) -> list[TransactionRecord]:
        """Return the requested item or information if it exists."""
        all_records = []
        for records in self._history.values():
            all_records.extend(records)
        all_records.sort(key=lambda r: r.timestamp)
        return all_records


# ─── Projection 3: Daily Summary ─────────────────────────────────


@dataclass
class DailySummary:
    """Represents DailySummary in this learning project."""
    date: str
    total_deposits: float = 0.0
    total_withdrawals: float = 0.0
    total_transfers: float = 0.0
    transaction_count: int = 0
    accounts_opened: int = 0


class DailySummaryProjection:
    """
    Aggregates events by day.
    Optimized for: "What happened on date X?" / "Show daily report."
    """

    def __init__(self):
        """Initialize the object with the dependencies or starting values it needs."""
        self._summaries: dict[str, DailySummary] = {}

    def handle_event(self, event: DomainEvent) -> None:
        """Handle one incoming command, event, request, or workflow step."""
        date = event.timestamp[:10]  # Extract YYYY-MM-DD
        if date not in self._summaries:
            self._summaries[date] = DailySummary(date=date)

        summary = self._summaries[date]
        summary.transaction_count += 1

        if event.event_type == "AccountOpened":
            summary.accounts_opened += 1
            summary.total_deposits += event.data.get("initial_deposit", 0.0)
        elif event.event_type == "MoneyDeposited":
            summary.total_deposits += event.data.get("amount", 0.0)
        elif event.event_type == "MoneyWithdrawn":
            summary.total_withdrawals += event.data.get("amount", 0.0)
        elif event.event_type in ("TransferInitiated",):
            summary.total_transfers += event.data.get("amount", 0.0)

    def get_summary(self, date: str) -> DailySummary | None:
        """Return the requested item or information if it exists."""
        return self._summaries.get(date)

    def get_all_summaries(self) -> list[DailySummary]:
        """Return the requested item or information if it exists."""
        return sorted(self._summaries.values(), key=lambda s: s.date)
