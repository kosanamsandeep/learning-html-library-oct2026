"""
PROJECT 14: STATE MACHINE - E-Commerce Order Workflow
=====================================================
Patterns: State Pattern, Finite State Machine, Guards, Transitions
Inspired by: XState (JS), django-fsm, Spring Statemachine, Erlang gen_statem

Story: You're building an e-commerce platform. Orders go through complex
lifecycle states (draft -> payment -> processing -> shipping -> delivery).
A state machine prevents impossible transitions and enforces business rules.

Key Concepts Demonstrated:
  1. Finite State Machine (FSM) engine
  2. Guard conditions (business rule enforcement)
  3. Entry/Exit actions per state
  4. Transition actions (side effects)
  5. Event history / audit trail
  6. Fluent builder interface
"""

import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from machine.fsm import StateMachine, StateConfig, Transition, TransitionResult
from models.order import Order, OrderItem, PaymentMethod
from workflows.order_workflow import create_order_workflow


def print_header():
    """Perform the print header step used by this project."""
    print("=" * 70)
    print("#  PROJECT 14: STATE MACHINE - E-Commerce Order Workflow")
    print("#  Patterns: FSM, State Pattern, Guards, Transitions")
    print("#  Inspired by: XState, django-fsm, Spring Statemachine")
    print("=" * 70)


def print_state(machine: StateMachine, label: str = ""):
    """Helper to show current state nicely."""
    state = machine.current_state
    events = machine.available_events()
    is_final = machine.is_in_final_state()
    marker = " [FINAL]" if is_final else ""
    if label:
        print(f"    {label}")
    print(f"    State: [{state}]{marker} | Available events: {events}")


def demo_1_happy_path():
    """Demo: Complete order lifecycle - happy path."""
    print("\n" + "=" * 70)
    print("  DEMO 1: Happy Path - Order Lifecycle")
    print("=" * 70)

    order = Order(
        order_id="ORD-001",
        customer_name="Alice Johnson",
        items=[
            OrderItem("Mechanical Keyboard", 1, 149.99),
            OrderItem("Mouse Pad", 2, 24.99),
        ],
        shipping_address="123 Tech Street, San Francisco, CA 94105",
    )

    print(f"\n  Order: {order.order_id} | Customer: {order.customer_name}")
    print(f"  Items: {len(order.items)} | Total: ${order.total_amount:.2f}")

    machine = create_order_workflow(order)

    # Walk through the happy path
    events = ["submit", "pay", "start_processing", "ship", "deliver"]

    print(f"\n  Walking through order lifecycle:\n")
    print_state(machine, "Initial state:")

    for event in events:
        result = machine.send(event)
        symbol = ">>>" if result.success else "XXX"
        print(f"\n    {symbol} Event: '{event}'")
        if result.success:
            print(f"        {result.from_state} -> {result.to_state}")
        else:
            print(f"        FAILED: {result.error}")
        print_state(machine)

    print(f"\n  Order Notes (audit trail):")
    for note in order.notes:
        print(f"    {note}")


def demo_2_guard_conditions():
    """Demo: Guards preventing invalid transitions."""
    print("\n" + "=" * 70)
    print("  DEMO 2: Guard Conditions (Business Rule Enforcement)")
    print("=" * 70)

    # Case 1: Empty cart (total = 0)
    print("\n  Case 1: Submit with empty cart")
    empty_order = Order(order_id="ORD-002", customer_name="Bob", items=[])
    m1 = create_order_workflow(empty_order)
    result = m1.send("submit")
    print(f"    Order total: ${empty_order.total_amount:.2f}")
    print(f"    Submit result: {'OK' if result.success else 'BLOCKED'}")
    print(f"    Reason: Guard requires total_amount > 0")

    # Case 2: Ship without address
    print("\n  Case 2: Ship without shipping address")
    no_addr_order = Order(
        order_id="ORD-003",
        customer_name="Charlie",
        items=[OrderItem("Book", 1, 29.99)],
        shipping_address="",  # No address!
    )
    m2 = create_order_workflow(no_addr_order)
    m2.send("submit")
    m2.send("pay")
    m2.send("start_processing")
    result = m2.send("ship")
    print(f"    Shipping address: '{no_addr_order.shipping_address}'")
    print(f"    Ship result: {'OK' if result.success else 'BLOCKED'}")
    print(f"    Reason: Guard requires non-empty shipping_address")
    print(f"    Current state: [{m2.current_state}] (stuck in processing!)")

    # Case 3: Invalid event for current state
    print("\n  Case 3: Invalid event for current state")
    order3 = Order(
        order_id="ORD-004",
        customer_name="Diana",
        items=[OrderItem("Phone", 1, 999.99)],
        shipping_address="456 Main St",
    )
    m3 = create_order_workflow(order3)
    result = m3.send("ship")  # Can't ship from draft!
    print(f"    State: [{m3.current_state}] | Event: 'ship'")
    print(f"    Result: {'OK' if result.success else 'BLOCKED'}")
    print(f"    Error: {result.error}")


def demo_3_payment_retry():
    """Demo: Payment failure and retry with max attempts."""
    print("\n" + "=" * 70)
    print("  DEMO 3: Payment Retry Logic (Max 3 Attempts)")
    print("=" * 70)

    order = Order(
        order_id="ORD-005",
        customer_name="Eve",
        items=[OrderItem("Laptop", 1, 1299.99)],
        shipping_address="789 Oak Ave",
    )
    machine = create_order_workflow(order)
    machine.send("submit")

    print(f"\n  Simulating payment failures:")
    print_state(machine)

    # Attempt 1: fail
    machine.send("payment_fail")
    print(f"\n    Attempt 1: FAILED")
    print(f"    Attempts: {machine.context['payment_attempts']}/3")
    print_state(machine)

    # Retry
    machine.send("retry_payment")
    print(f"\n    Retrying payment...")
    print_state(machine)

    # Attempt 2: fail
    machine.send("payment_fail")
    print(f"\n    Attempt 2: FAILED")
    print(f"    Attempts: {machine.context['payment_attempts']}/3")

    # Retry
    machine.send("retry_payment")

    # Attempt 3: fail
    machine.send("payment_fail")
    print(f"\n    Attempt 3: FAILED")
    print(f"    Attempts: {machine.context['payment_attempts']}/3")

    # Try to retry again (should be blocked by guard)
    result = machine.send("retry_payment")
    print(f"\n    Retry attempt 4: {'ALLOWED' if result.success else 'BLOCKED'}")
    print(f"    Guard: payment_attempts < 3 -> False (3 >= 3)")

    # Cancel the order
    machine.send("cancel")
    print(f"\n    Final state: [{machine.current_state}]")
    print(f"    Reason: {machine.context['cancelled_reason']}")


def demo_4_cancellation_refund():
    """Demo: Cancellation and refund at different stages."""
    print("\n" + "=" * 70)
    print("  DEMO 4: Cancellation & Refund Paths")
    print("=" * 70)

    # Cancel from draft
    print("\n  Case 1: Cancel from draft")
    o1 = Order(
        order_id="ORD-006",
        customer_name="Frank",
        items=[OrderItem("Hat", 1, 49.99)],
        shipping_address="addr",
    )
    m1 = create_order_workflow(o1)
    m1.send("cancel")
    print(f"    draft -> cancel = [{m1.current_state}]")

    # Cancel after payment (should be possible)
    print("\n  Case 2: Cancel after payment")
    o2 = Order(
        order_id="ORD-007",
        customer_name="Grace",
        items=[OrderItem("Shoes", 1, 199.99)],
        shipping_address="addr",
    )
    m2 = create_order_workflow(o2)
    m2.send("submit")
    m2.send("pay")
    m2.send("cancel")
    print(f"    paid -> cancel = [{m2.current_state}]")

    # Refund after payment
    print("\n  Case 3: Full refund from paid state")
    o3 = Order(
        order_id="ORD-008",
        customer_name="Henry",
        items=[OrderItem("Watch", 1, 499.99)],
        shipping_address="addr",
    )
    m3 = create_order_workflow(o3)
    m3.send("submit")
    m3.send("pay")
    m3.send("refund")
    print(f"    paid -> refund = [{m3.current_state}]")
    print(f"    Refund amount: ${m3.context['refund_amount']:.2f} (100%)")

    # Partial refund after delivery
    print("\n  Case 4: Partial refund after delivery (80%)")
    o4 = Order(
        order_id="ORD-009",
        customer_name="Iris",
        items=[OrderItem("Tablet", 1, 799.99)],
        shipping_address="addr",
    )
    m4 = create_order_workflow(o4)
    for event in ["submit", "pay", "start_processing", "ship", "deliver"]:
        m4.send(event)
    m4.send("refund")
    print(f"    delivered -> refund = [{m4.current_state}]")
    print(
        f"    Refund amount: ${m4.context['refund_amount']:.2f} (80% of ${o4.total_amount:.2f})"
    )

    # Cannot cancel after shipping
    print("\n  Case 5: Cannot cancel after shipping")
    o5 = Order(
        order_id="ORD-010",
        customer_name="Jack",
        items=[OrderItem("Camera", 1, 1299.99)],
        shipping_address="addr",
    )
    m5 = create_order_workflow(o5)
    for event in ["submit", "pay", "start_processing", "ship"]:
        m5.send(event)
    result = m5.send("cancel")
    print(f"    shipped -> cancel = {'ALLOWED' if result.success else 'BLOCKED'}")
    print(f"    (No transition defined for 'cancel' in 'shipped' state)")


def demo_5_observer_audit():
    """Demo: Transition observer and full audit trail."""
    print("\n" + "=" * 70)
    print("  DEMO 5: Observer Pattern & Audit Trail")
    print("=" * 70)

    order = Order(
        order_id="ORD-011",
        customer_name="Karen",
        items=[
            OrderItem("Gaming Monitor", 1, 549.99),
            OrderItem("HDMI Cable", 2, 14.99),
        ],
        shipping_address="101 Gamer Blvd, Austin, TX 78701",
    )

    machine = create_order_workflow(order)

    # Register observer
    transitions_log = []

    def log_transition(result: TransitionResult):
        """Perform the log transition step used by this project."""
        if result.success:
            transitions_log.append(
                f"{result.from_state} --[{result.event}]--> {result.to_state}"
            )

    machine.on_transition(log_transition)

    # Execute full lifecycle
    for event in ["submit", "pay", "start_processing", "ship", "deliver"]:
        machine.send(event)

    print(f"\n  Transition Log (Observer Pattern):")
    for i, entry in enumerate(transitions_log, 1):
        print(f"    {i}. {entry}")

    print(f"\n  Full History (including failed attempts):")
    for i, result in enumerate(machine.history, 1):
        status = "OK" if result.success else "FAIL"
        print(
            f"    {i}. [{status}] {result.from_state} --[{result.event}]--> {result.to_state or '?'}"
        )

    print(f"\n  Order Audit Notes:")
    for note in order.notes:
        print(f"    {note}")


def print_summary():
    """Perform the print summary step used by this project."""
    print("\n" + "=" * 70)
    print("  LEARNING SUMMARY")
    print("=" * 70)
    print("""
  FINITE STATE MACHINE (FSM):
     - Entity has a CURRENT STATE
     - EVENTS trigger TRANSITIONS between states
     - Only VALID transitions are allowed
     - Invalid events are rejected (no silent corruption)

  GUARD CONDITIONS:
     - Business rules that gate transitions
     - e.g., "can only ship if address exists"
     - Prevent impossible scenarios at the design level

  ENTRY/EXIT ACTIONS:
     - Side effects tied to state changes
     - on_enter: runs when entering a state
     - on_exit: runs when leaving a state
     - Keeps business logic declarative

  STATE MACHINE vs IF/ELSE:
     - if/else: scattered checks, easy to miss edge cases
     - FSM: centralized rules, impossible to reach invalid states
     - FSM: self-documenting (the diagram IS the code)

  REAL-WORLD USAGE:
     - XState (JavaScript): UI component state
     - django-fsm: Model lifecycle in Django
     - AWS Step Functions: Workflow orchestration
     - Game dev: Character states (idle, walk, jump, attack)
     - Network protocols: TCP connection states
    """)


if __name__ == "__main__":
    print_header()
    demo_1_happy_path()
    demo_2_guard_conditions()
    demo_3_payment_retry()
    demo_4_cancellation_refund()
    demo_5_observer_audit()
    print_summary()
