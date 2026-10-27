"""
PROJECT 15: CQRS & EVENT SOURCING - Banking Ledger
===================================================
Patterns: CQRS, Event Sourcing, Aggregate Root, Projections
Inspired by: EventStoreDB, Axon Framework, Greg Young, Martin Fowler

Story: You're building a banking system where every transaction must be
auditable, reversible, and provable. Instead of mutating state in a database,
you store the sequence of events. Current state = replay all events.

Key Concepts Demonstrated:
  1. Event Sourcing (append-only event log)
  2. CQRS (separate read and write models)
  3. Aggregate Root (business logic enforcement)
  4. Projections (multiple read models from same events)
  5. Event replay (rebuild state from history)
"""

import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from events.event_store import EventStore
from commands.handlers import (
    BankCommandHandler,
    OpenAccountCommand,
    DepositCommand,
    WithdrawCommand,
    TransferCommand,
    FreezeAccountCommand,
)
from projections.read_models import (
    BalanceProjection,
    TransactionHistoryProjection,
    DailySummaryProjection,
)
from queries.handlers import (
    BankQueryHandler,
    GetBalanceQuery,
    GetTransactionHistoryQuery,
    GetAllAccountsQuery,
)


def create_bank_system():
    """Wire up the full CQRS system."""
    # Event Store (single source of truth)
    store = EventStore()

    # Projections (read models)
    balance_proj = BalanceProjection()
    history_proj = TransactionHistoryProjection()
    daily_proj = DailySummaryProjection()

    # Subscribe projections to event store
    store.subscribe(balance_proj)
    store.subscribe(history_proj)
    store.subscribe(daily_proj)

    # Command handler (write side)
    cmd_handler = BankCommandHandler(store)

    # Query handler (read side)
    query_handler = BankQueryHandler(balance_proj, history_proj, daily_proj)

    return store, cmd_handler, query_handler


def print_header():
    """Perform the print header step used by this project."""
    print("=" * 70)
    print("#  PROJECT 15: CQRS & EVENT SOURCING - Banking Ledger")
    print("#  Patterns: CQRS, Event Sourcing, Aggregates, Projections")
    print("#  Inspired by: EventStoreDB, Axon Framework, Greg Young")
    print("=" * 70)


def demo_1_event_sourcing():
    """Demo: Events as source of truth."""
    print("\n" + "=" * 70)
    print("  DEMO 1: Event Sourcing (Append-Only Event Log)")
    print("=" * 70)

    store, cmd, query = create_bank_system()

    print("\n  Creating accounts and performing transactions:")
    results = [
        cmd.handle_open_account(OpenAccountCommand("ACC-001", "Alice", 1000.0)),
        cmd.handle_open_account(OpenAccountCommand("ACC-002", "Bob", 500.0)),
        cmd.handle_deposit(DepositCommand("ACC-001", 250.0, "Salary bonus")),
        cmd.handle_withdraw(WithdrawCommand("ACC-001", 100.0, "Groceries")),
        cmd.handle_deposit(DepositCommand("ACC-002", 750.0, "Freelance work")),
    ]

    for r in results:
        print(f"    {r}")

    print(f"\n  Event Store Contents ({store.event_count} events):")
    for i, event in enumerate(store.get_all_events(), 1):
        print(
            f"    {i}. [{event.event_type:20s}] account={event.aggregate_id} "
            f"| data={event.data}"
        )

    print("\n  Key insight: We stored EVENTS, not current state.")
    print("  State is derived by replaying events.")

    # Show derived state
    print(f"\n  Derived state (by replaying events):")
    acct = query.get_balance(GetBalanceQuery("ACC-001"))
    print(f"    Alice: ${acct.balance:.2f} ({acct.transaction_count} transactions)")
    acct = query.get_balance(GetBalanceQuery("ACC-002"))
    print(f"    Bob:   ${acct.balance:.2f} ({acct.transaction_count} transactions)")


def demo_2_cqrs_separation():
    """Demo: Separate write (commands) and read (queries) paths."""
    print("\n" + "=" * 70)
    print("  DEMO 2: CQRS - Command/Query Separation")
    print("=" * 70)

    store, cmd, query = create_bank_system()

    # WRITE side: Commands (imperative)
    print("\n  WRITE SIDE (Commands - what we WANT to do):")
    commands = [
        (
            "OpenAccount",
            cmd.handle_open_account(OpenAccountCommand("ACC-100", "Charlie", 2000.0)),
        ),
        ("Deposit", cmd.handle_deposit(DepositCommand("ACC-100", 500.0, "Gift"))),
        ("Withdraw", cmd.handle_withdraw(WithdrawCommand("ACC-100", 300.0, "Rent"))),
        (
            "Withdraw",
            cmd.handle_withdraw(WithdrawCommand("ACC-100", 5000.0, "Too much")),
        ),  # Should fail
    ]
    for name, result in commands:
        print(f"    [{name:15s}] {result}")

    # READ side: Queries (declarative)
    print("\n  READ SIDE (Queries - what we WANT to know):")
    balance = query.get_balance(GetBalanceQuery("ACC-100"))
    print(f"    Balance: ${balance.balance:.2f}")
    print(f"    Owner: {balance.owner_name}")
    print(f"    Frozen: {balance.is_frozen}")
    print(f"    Transactions: {balance.transaction_count}")

    history = query.get_history(GetTransactionHistoryQuery("ACC-100"))
    print(f"\n    Transaction History:")
    for tx in history:
        sign = "+" if tx.amount > 0 else ""
        print(
            f"      {sign}{tx.amount:>10.2f} | {tx.description:20s} | bal: ${tx.balance_after:.2f}"
        )

    print("\n  Key insight: Commands WRITE events. Queries READ projections.")
    print("  They use DIFFERENT models optimized for their purpose.")


def demo_3_transfers():
    """Demo: Multi-aggregate transactions via events."""
    print("\n" + "=" * 70)
    print("  DEMO 3: Fund Transfers (Multi-Aggregate Coordination)")
    print("=" * 70)

    store, cmd, query = create_bank_system()

    # Setup accounts
    cmd.handle_open_account(OpenAccountCommand("ACC-A", "Alice", 5000.0))
    cmd.handle_open_account(OpenAccountCommand("ACC-B", "Bob", 1000.0))
    cmd.handle_open_account(OpenAccountCommand("ACC-C", "Charlie", 2000.0))

    print("\n  Initial balances:")
    for acc_id in ["ACC-A", "ACC-B", "ACC-C"]:
        bal = query.get_balance(GetBalanceQuery(acc_id))
        print(f"    {bal.owner_name}: ${bal.balance:.2f}")

    # Perform transfers
    print("\n  Transfers:")
    results = [
        cmd.handle_transfer(TransferCommand("ACC-A", "ACC-B", 1500.0, "Loan to Bob")),
        cmd.handle_transfer(TransferCommand("ACC-B", "ACC-C", 800.0, "Pay Charlie")),
        cmd.handle_transfer(
            TransferCommand("ACC-A", "ACC-C", 10000.0, "Too much")
        ),  # Should fail
    ]
    for r in results:
        print(f"    {r}")

    print("\n  Final balances:")
    for acc_id in ["ACC-A", "ACC-B", "ACC-C"]:
        bal = query.get_balance(GetBalanceQuery(acc_id))
        print(f"    {bal.owner_name}: ${bal.balance:.2f}")

    # Show transfer events
    print(f"\n  Events emitted for transfers:")
    for event in store.get_all_events():
        if "Transfer" in event.event_type:
            print(
                f"    {event.event_type:20s} | account={event.aggregate_id} | amount=${event.data.get('amount', 0):.2f}"
            )


def demo_4_business_rules():
    """Demo: Business rule enforcement via aggregates."""
    print("\n" + "=" * 70)
    print("  DEMO 4: Business Rules (Aggregate Guards)")
    print("=" * 70)

    store, cmd, query = create_bank_system()
    cmd.handle_open_account(OpenAccountCommand("ACC-X", "Xavier", 1000.0))

    tests = [
        (
            "Overdraw",
            cmd.handle_withdraw(WithdrawCommand("ACC-X", 2000.0, "Overdraw attempt")),
        ),
        ("Negative deposit", cmd.handle_deposit(DepositCommand("ACC-X", -100.0))),
        ("Non-existent account", cmd.handle_deposit(DepositCommand("ACC-999", 100.0))),
        (
            "Duplicate account",
            cmd.handle_open_account(OpenAccountCommand("ACC-X", "Duplicate", 0.0)),
        ),
    ]

    print("\n  Testing business rule enforcement:")
    for name, result in tests:
        status = "BLOCKED" if "ERROR" in result else "OK"
        print(f"    [{status:7s}] {name}: {result}")

    # Freeze account
    print("\n  Freezing account:")
    print(
        f"    {cmd.handle_freeze(FreezeAccountCommand('ACC-X', 'Suspicious activity'))}"
    )
    print(f"    {cmd.handle_deposit(DepositCommand('ACC-X', 100.0, 'Try deposit'))}")
    print(f"    {cmd.handle_withdraw(WithdrawCommand('ACC-X', 50.0, 'Try withdraw'))}")

    print("\n  Key insight: Business rules are enforced in the AGGREGATE,")
    print("  which rebuilds its state from events before validating.")


def demo_5_projection_rebuild():
    """Demo: Projections can be rebuilt from events."""
    print("\n" + "=" * 70)
    print("  DEMO 5: Projection Rebuild (Time Travel)")
    print("=" * 70)

    store, cmd, query = create_bank_system()

    # Create some history
    cmd.handle_open_account(OpenAccountCommand("ACC-TT", "TimeTravel", 1000.0))
    cmd.handle_deposit(DepositCommand("ACC-TT", 500.0, "Deposit 1"))
    cmd.handle_withdraw(WithdrawCommand("ACC-TT", 200.0, "Withdraw 1"))
    cmd.handle_deposit(DepositCommand("ACC-TT", 300.0, "Deposit 2"))
    cmd.handle_withdraw(WithdrawCommand("ACC-TT", 150.0, "Withdraw 2"))

    current = query.get_balance(GetBalanceQuery("ACC-TT"))
    print(f"\n  Current balance: ${current.balance:.2f}")
    print(f"  Events in stream: {len(store.get_stream('ACC-TT'))}")

    # Rebuild projection from scratch (simulating a new projection)
    print("\n  Rebuilding a FRESH projection from event stream:")
    from projections.read_models import BalanceProjection

    fresh_projection = BalanceProjection()

    # Replay events one by one (time travel!)
    events = store.get_stream("ACC-TT")
    print(f"\n  Replaying {len(events)} events:")
    for i, event in enumerate(events, 1):
        fresh_projection.handle_event(event)
        state = fresh_projection.get_balance("ACC-TT")
        balance = state.balance if state else 0
        print(f"    Event {i}: {event.event_type:20s} -> Balance: ${balance:.2f}")

    rebuilt = fresh_projection.get_balance("ACC-TT")
    print(f"\n  Rebuilt balance: ${rebuilt.balance:.2f}")
    print(f"  Matches current: {rebuilt.balance == current.balance}")
    print(f"\n  Key insight: Projections are DISPOSABLE.")
    print("  Delete them, replay events, get same state.")
    print("  This enables: schema migrations, new read models, bug fixes.")


def print_summary():
    """Perform the print summary step used by this project."""
    print("\n" + "=" * 70)
    print("  LEARNING SUMMARY")
    print("=" * 70)
    print("""
  EVENT SOURCING:
     - Store EVENTS (facts), not current state
     - Events are immutable and append-only
     - Current state = fold(initial_state, all_events)
     - Full audit trail for free
     - Can "time travel" to any point in history

  CQRS (Command Query Responsibility Segregation):
     - WRITE side: Commands -> Validate -> Emit events
     - READ side: Queries -> Read from projections
     - Different models for reads vs writes
     - Read models are denormalized and fast

  AGGREGATES:
     - Enforce business rules before emitting events
     - Rebuild state from event stream
     - Consistency boundary (all rules in one place)
     - One aggregate = one event stream

  PROJECTIONS:
     - Build optimized read models from events
     - Multiple projections from same events
     - Disposable: rebuild by replaying
     - Eventually consistent with write side

  REAL-WORLD USAGE:
     - EventStoreDB: Purpose-built event store
     - Apache Kafka: Event streaming platform
     - Axon Framework (Java): Full CQRS/ES framework
     - Banking: Every transaction is an event
     - Git: Commits are events, working tree is projection
    """)


if __name__ == "__main__":
    print_header()
    demo_1_event_sourcing()
    demo_2_cqrs_separation()
    demo_3_transfers()
    demo_4_business_rules()
    demo_5_projection_rebuild()
    print_summary()
