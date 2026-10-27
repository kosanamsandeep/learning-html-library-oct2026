"""
Command Handlers - The WRITE side of CQRS.

Commands represent INTENT (what the user wants to do).
Named in imperative: OpenAccount, DepositMoney, TransferFunds.

Command handlers:
  1. Validate the command
  2. Load aggregate state (by replaying events)
  3. Apply business rules
  4. Emit new events (if valid)

The command side NEVER reads from projections — it only reads events.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from events.event_store import (
    EventStore,
    DomainEvent,
    AccountOpened,
    MoneyDeposited,
    MoneyWithdrawn,
    TransferInitiated,
    TransferCompleted,
    TransferFailed,
    AccountFrozen,
    AccountClosed,
)

# ─── Commands (DTOs representing intent) ─────────────────────────


@dataclass
class OpenAccountCommand:
    """Represents a user intention that should change application state."""
    account_id: str
    owner_name: str
    initial_deposit: float = 0.0
    account_type: str = "checking"


@dataclass
class DepositCommand:
    """Represents a user intention that should change application state."""
    account_id: str
    amount: float
    description: str = ""


@dataclass
class WithdrawCommand:
    """Represents a user intention that should change application state."""
    account_id: str
    amount: float
    description: str = ""


@dataclass
class TransferCommand:
    """Represents a user intention that should change application state."""
    from_account_id: str
    to_account_id: str
    amount: float
    description: str = ""


@dataclass
class FreezeAccountCommand:
    """Represents a user intention that should change application state."""
    account_id: str
    reason: str = ""


@dataclass
class CloseAccountCommand:
    """Represents a user intention that should change application state."""
    account_id: str


# ─── Aggregate (rebuilds state from events) ──────────────────────


class BankAccountAggregate:
    """
    Aggregate root for a bank account.
    State is NEVER stored directly — it's always rebuilt from events.

    This is the key insight of Event Sourcing:
    current_state = reduce(apply_event, events, initial_state)
    """

    
    def __init__(self):
        """Initialize the object with the dependencies or starting values it needs."""
        self.account_id: str = ""
        self.owner_name: str = ""
        self.balance: float = 0.0
        self.is_frozen: bool = False
        self.is_closed: bool = False
        self.account_type: str = "checking"
        self.version: int = 0

    def apply(self, event: DomainEvent) -> None:
        """Apply an event to update aggregate state (event handler)."""
        self.version += 1

        if event.event_type == "AccountOpened":
            self.account_id = event.aggregate_id
            self.owner_name = event.data.get("owner_name", "")
            self.balance = event.data.get("initial_deposit", 0.0)
            self.account_type = event.data.get("account_type", "checking")

        elif event.event_type == "MoneyDeposited":
            self.balance += event.data.get("amount", 0.0)

        elif event.event_type == "MoneyWithdrawn":
            self.balance -= event.data.get("amount", 0.0)

        elif event.event_type == "TransferInitiated":
            # Debit from source
            if event.aggregate_id == self.account_id:
                self.balance -= event.data.get("amount", 0.0)

        elif event.event_type == "TransferCompleted":
            # Credit to destination
            if event.aggregate_id == self.account_id:
                self.balance += event.data.get("amount", 0.0)

        elif event.event_type == "TransferFailed":
            # Reverse the debit
            if event.aggregate_id == event.data.get("from_account_id"):
                self.balance += event.data.get("amount", 0.0)

        elif event.event_type == "AccountFrozen":
            self.is_frozen = True

        elif event.event_type == "AccountClosed":
            self.is_closed = True

    @classmethod
    def from_events(cls, events: list[DomainEvent]) -> "BankAccountAggregate":
        """Rebuild aggregate state by replaying events."""
        aggregate = cls()
        for event in events:
            aggregate.apply(event)
        return aggregate


# ─── Command Handler ──────────────────────────────────────────────


class BankCommandHandler:
    """
    Handles commands by:
    1. Loading aggregate from event stream
    2. Validating business rules
    3. Emitting events if valid

    This is the WRITE side of CQRS.
    """

    def __init__(self, event_store: EventStore):
        """Initialize the object with the dependencies or starting values it needs."""
        self._store = event_store

    def _load_aggregate(self, account_id: str) -> BankAccountAggregate:
        """Load account state by replaying its event stream."""
        events = self._store.get_stream(account_id)
        return BankAccountAggregate.from_events(events)

    def handle_open_account(self, cmd: OpenAccountCommand) -> str:
        """Open a new bank account."""
        # Validate: account doesn't already exist
        existing = self._store.get_stream(cmd.account_id)
        if existing:
            return f"ERROR: Account {cmd.account_id} already exists"

        if cmd.initial_deposit < 0:
            return f"ERROR: Initial deposit cannot be negative"

        # Emit event
        event = AccountOpened(
            aggregate_id=cmd.account_id,
            version=1,
            data={
                "owner_name": cmd.owner_name,
                "initial_deposit": cmd.initial_deposit,
                "account_type": cmd.account_type,
            },
        )
        self._store.append(event)
        return f"OK: Account {cmd.account_id} opened for {cmd.owner_name}"

    def handle_deposit(self, cmd: DepositCommand) -> str:
        """Deposit money into an account."""
        aggregate = self._load_aggregate(cmd.account_id)

        if not aggregate.account_id:
            return f"ERROR: Account {cmd.account_id} not found"
        if aggregate.is_frozen:
            return f"ERROR: Account {cmd.account_id} is frozen"
        if aggregate.is_closed:
            return f"ERROR: Account {cmd.account_id} is closed"
        if cmd.amount <= 0:
            return f"ERROR: Deposit amount must be positive"

        event = MoneyDeposited(
            aggregate_id=cmd.account_id,
            version=aggregate.version + 1,
            data={"amount": cmd.amount, "description": cmd.description},
        )
        self._store.append(event)
        return f"OK: Deposited ${cmd.amount:.2f} to {cmd.account_id}"

    def handle_withdraw(self, cmd: WithdrawCommand) -> str:
        """Withdraw money from an account."""
        aggregate = self._load_aggregate(cmd.account_id)

        if not aggregate.account_id:
            return f"ERROR: Account {cmd.account_id} not found"
        if aggregate.is_frozen:
            return f"ERROR: Account {cmd.account_id} is frozen"
        if aggregate.is_closed:
            return f"ERROR: Account {cmd.account_id} is closed"
        if cmd.amount <= 0:
            return f"ERROR: Withdrawal amount must be positive"
        if aggregate.balance < cmd.amount:
            return f"ERROR: Insufficient funds (balance: ${aggregate.balance:.2f})"

        event = MoneyWithdrawn(
            aggregate_id=cmd.account_id,
            version=aggregate.version + 1,
            data={"amount": cmd.amount, "description": cmd.description},
        )
        self._store.append(event)
        return f"OK: Withdrew ${cmd.amount:.2f} from {cmd.account_id}"

    def handle_transfer(self, cmd: TransferCommand) -> str:
        """Transfer money between accounts."""
        source = self._load_aggregate(cmd.from_account_id)
        dest = self._load_aggregate(cmd.to_account_id)

        if not source.account_id:
            return f"ERROR: Source account {cmd.from_account_id} not found"
        if not dest.account_id:
            return f"ERROR: Destination account {cmd.to_account_id} not found"
        if source.is_frozen:
            return f"ERROR: Source account is frozen"
        if dest.is_frozen:
            return f"ERROR: Destination account is frozen"
        if cmd.amount <= 0:
            return f"ERROR: Transfer amount must be positive"
        if source.balance < cmd.amount:
            return f"ERROR: Insufficient funds (balance: ${source.balance:.2f})"

        # Emit transfer initiated (debits source)
        init_event = TransferInitiated(
            aggregate_id=cmd.from_account_id,
            version=source.version + 1,
            data={
                "amount": cmd.amount,
                "from_account_id": cmd.from_account_id,
                "to_account_id": cmd.to_account_id,
                "description": cmd.description,
            },
        )
        self._store.append(init_event)

        # Emit transfer completed (credits destination)
        complete_event = TransferCompleted(
            aggregate_id=cmd.to_account_id,
            version=dest.version + 1,
            data={
                "amount": cmd.amount,
                "from_account_id": cmd.from_account_id,
                "to_account_id": cmd.to_account_id,
            },
        )
        self._store.append(complete_event)

        return f"OK: Transferred ${cmd.amount:.2f} from {cmd.from_account_id} to {cmd.to_account_id}"

    def handle_freeze(self, cmd: FreezeAccountCommand) -> str:
        """Freeze an account."""
        aggregate = self._load_aggregate(cmd.account_id)
        if not aggregate.account_id:
            return f"ERROR: Account {cmd.account_id} not found"

        event = AccountFrozen(
            aggregate_id=cmd.account_id,
            version=aggregate.version + 1,
            data={"reason": cmd.reason},
        )
        self._store.append(event)
        return f"OK: Account {cmd.account_id} frozen ({cmd.reason})"

    def handle_close(self, cmd: CloseAccountCommand) -> str:
        """Close an account (must have zero balance)."""
        aggregate = self._load_aggregate(cmd.account_id)
        if not aggregate.account_id:
            return f"ERROR: Account {cmd.account_id} not found"
        if aggregate.balance != 0:
            return f"ERROR: Cannot close account with balance ${aggregate.balance:.2f}"

        event = AccountClosed(
            aggregate_id=cmd.account_id,
            version=aggregate.version + 1,
            data={},
        )
        self._store.append(event)
        return f"OK: Account {cmd.account_id} closed"
