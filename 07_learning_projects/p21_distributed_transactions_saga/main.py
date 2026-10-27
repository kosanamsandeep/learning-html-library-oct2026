"""
P21 - Distributed Transactions with the Saga Pattern
=====================================================
5 Demos showing how to keep data consistent across multiple microservices
without a single distributed (2PC) transaction.

Inspired by: Netflix, AWS Step Functions, NServiceBus, Debezium (Outbox)
Patterns: Choreographed Saga, Orchestrated Saga, Compensating Transaction,
          Transactional Outbox, Idempotency Keys, Saga State Machine
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

from saga.choreography import EventBus, SagaEvent, Service
from saga.idempotency import IdempotencyStore
from saga.orchestrator import OrchestratedSaga, SagaStatus
from saga.outbox import OutboxDispatcher, OutboxStore


class OutOfStockError(Exception):
    """Raised when inventory cannot satisfy an order."""


class PaymentRejectedError(Exception):
    """Raised when a card payment is declined."""


class CarrierApiError(Exception):
    """Raised when the shipping carrier API fails."""


def demo_1_choreographed_saga():
    """Demo 1: Event-driven saga with no central coordinator."""
    print("=" * 70)
    print("DEMO 1: Choreographed Saga (No Central Coordinator)")
    print("=" * 70)
    print("Story: Order → Payment → Inventory → Shipping. Each service reacts\n"
          "       to the previous event. Inventory is out of stock, so the\n"
          "       failure event ripples backward as compensation.\n")

    bus = EventBus()
    order = Service("order", bus)
    payment = Service("payment", bus)
    inventory = Service("inventory", bus)
    shipping = Service("shipping", bus)

    stock = {"Widget": 2}

    def charge(event):
        print(f"    [payment] Charging ${99.99:.2f} ... OK")

    def reserve(event):
        qty = event.payload["qty"]
        available = stock[event.payload["product"]]
        if available < qty:
            raise OutOfStockError(f"only {available} in stock, need {qty}")
        stock[event.payload["product"]] -= qty
        print(f"    [inventory] Reserved {qty} x {event.payload['product']}")

    def refund(event):
        print(f"    [payment] Refunding ${99.99:.2f} ... OK")

    def cancel_order(event):
        print(f"    [order] Order {event.payload['order_id']} CANCELLED")

    # Forward chain (happy path)
    order.subscribe_forward(
        "START", "ORDER_PLACED", lambda e: print("    [order] Order placed")
    )
    payment.subscribe_forward("ORDER_PLACED", "PAYMENT_CHARGED", charge)
    inventory.subscribe_forward("PAYMENT_CHARGED", "INVENTORY_RESERVED", reserve)
    shipping.subscribe_forward(
        "INVENTORY_RESERVED", "SHIPPED", lambda e: print("    [shipping] Package shipped")
    )

    # Compensation chain (reaction to failure)
    payment.subscribe_compensate("INVENTORY_RESERVED_FAILED", "PAYMENT_REFUNDED", refund)
    order.subscribe_compensate("PAYMENT_REFUNDED", "ORDER_CANCELLED", cancel_order)

    # Kick off the saga
    bus.publish(
        SagaEvent("START", "saga-100", {"order_id": "ORD-100", "product": "Widget", "qty": 5})
    )

    print("\n  Events delivered:")
    for ev in bus.delivered:
        src = ev.source or "external"
        print(f"    {ev.event_type:28s} <- {src}")

    # The happy path stopped at inventory; compensation completed the story
    delivered = [ev.event_type for ev in bus.delivered]
    assert "PAYMENT_CHARGED" in delivered
    assert "SHIPPED" not in delivered                    # inventory failed, nothing shipped
    assert "INVENTORY_RESERVED_FAILED" in delivered
    assert "PAYMENT_REFUNDED" in delivered
    assert "ORDER_CANCELLED" in delivered
    assert order.compensated == ["PAYMENT_REFUNDED"]
    assert payment.compensated == ["INVENTORY_RESERVED_FAILED"]
    print("\n  ✅ Demo 1 PASSED")


def demo_2_orchestrated_saga():
    """Demo 2: Central orchestrator runs steps and compensates in reverse."""
    print("\n" + "=" * 70)
    print("DEMO 2: Orchestrated Saga (Central Coordinator)")
    print("=" * 70)
    print("Story: A SagaOrchestrator calls services in order. When the final\n"
          "       step fails, every completed step is undone — in reverse order.\n")

    # --- Happy path ---
    print("  --- Saga A: all steps succeed ---")
    saga_a = OrchestratedSaga("saga-A", "order-placement")
    saga_a.add_step(
        "reserve_inventory",
        lambda: print("    reserve_inventory ......... OK"),
        lambda: print("    UNDO reserve_inventory (restock)"),
    )
    saga_a.add_step(
        "charge_card",
        lambda: print("    charge_card ............... OK"),
        lambda: print("    UNDO charge_card (refund)"),
    )
    saga_a.add_step(
        "confirm_shipment",
        lambda: print("    confirm_shipment .......... OK"),
        lambda: print("    UNDO confirm_shipment"),
    )
    ok_a = saga_a.run()
    print(f"    -> saga status: {saga_a.status.value}")
    assert ok_a is True and saga_a.status == SagaStatus.COMPLETED

    # --- Failure path ---
    print("\n  --- Saga B: shipment step fails ---")

    def failing_shipment():
        print("    confirm_shipment .......... FAILED (carrier API down)")
        raise CarrierApiError("carrier timeout")

    saga_b = OrchestratedSaga("saga-B", "order-placement")
    saga_b.add_step(
        "reserve_inventory",
        lambda: print("    reserve_inventory ......... OK"),
        lambda: print("    UNDO reserve_inventory (restock)"),
    )
    saga_b.add_step(
        "charge_card",
        lambda: print("    charge_card ............... OK"),
        lambda: print("    UNDO charge_card (refund)"),
    )
    saga_b.add_step("confirm_shipment", failing_shipment, lambda: print("    UNDO confirm_shipment"))
    ok_b = saga_b.run()
    print(f"    -> saga status: {saga_b.status.value}")

    print("\n  Compensation trace:")
    for line in saga_b.history:
        if "UNDO" in line or "COMPENSATING" in line or "FAILED" in line:
            print(f"    {line}")

    executed = [s.name for s in saga_b.steps if s.executed]
    compensated_set = {s.name for s in saga_b.steps if s.compensated}
    undo_order = [line.split("UNDO OK")[1].strip() for line in saga_b.history if "UNDO OK" in line]
    assert ok_b is False and saga_b.status == SagaStatus.FAILED
    assert executed == ["reserve_inventory", "charge_card"]
    assert compensated_set == {"charge_card", "reserve_inventory"}
    assert undo_order == ["charge_card", "reserve_inventory"]  # exact reverse execution order
    print("\n  ✅ Demo 2 PASSED")


def demo_3_transactional_outbox():
    """Demo 3: Atomic state write + reliable event emission via an outbox."""
    print("\n" + "=" * 70)
    print("DEMO 3: Transactional Outbox (Reliable Events)")
    print("=" * 70)
    print("Story: If we write state and then emit an event in two separate steps,\n"
          "       a crash between them loses the event. The outbox commits both\n"
          "       in ONE transaction; a dispatcher publishes the rows safely.\n")

    store = OutboxStore()
    orders = {}

    def create_order(order_id):
        store.atomic_write(
            lambda: orders.__setitem__(order_id, {"status": "created"}),
            order_id,
            "ORDER_CREATED",
            {"order_id": order_id},
        )

    create_order("ORD-1")
    create_order("ORD-2")
    create_order("ORD-3")
    create_order("ORD-4")
    print(f"  4 business writes -> {len(store.pending())} pending outbox events")
    assert len(store.pending()) == 4

    # First dispatcher poll flushes 2 events, then the process "crashes"
    dispatcher = OutboxDispatcher(store)
    flushed = dispatcher.poll(limit=2)
    print(f"  Poll #1 flushed {flushed} events  ->  [process crashes and restarts]")
    assert len(store.pending()) == 2

    # A NEW dispatcher sees the durable outbox and finishes the job
    restarted = OutboxDispatcher(store)
    flushed2 = restarted.poll()
    print(f"  Poll #2 (restarted process) flushed {flushed2} events")

    delivered = dispatcher.delivered + restarted.delivered
    print("\n  Total events delivered exactly once:", delivered)
    assert delivered == ["ORDER_CREATED"] * 4
    assert len(store.pending()) == 0
    assert orders == {oid: {"status": "created"} for oid in ("ORD-1", "ORD-2", "ORD-3", "ORD-4")}
    print("  ✅ No events lost, none duplicated. Demo 3 PASSED")


def demo_4_idempotency_keys():
    """Demo 4: Idempotency keys make retried saga steps exactly-once."""
    print("\n" + "=" * 70)
    print("DEMO 4: Idempotency Keys (Exactly-Once Under Retry)")
    print("=" * 70)
    print("Story: A network timeout makes the client retry a charge. Without\n"
          "       protection the customer is charged twice. The idempotency key\n"
          "       makes the retry return the first result instead.\n")

    store = IdempotencyStore()
    charges = []

    def charge(amount):
        charges.append(amount)
        return {"charged": amount, "charge_id": f"chg-{len(charges)}"}

    key = "idem-PAY-ORD-200"  # client supplies once per logical payment
    first, replayed_first = store.execute(key, lambda: charge(99.99))
    print("  Call 1 (original):", first, "| replayed?", replayed_first)

    # Network timeout -> client retries with the SAME key
    retry, replayed_retry = store.execute(key, lambda: charge(99.99))
    print("  Call 2 (retry, same key):", retry, "| replayed?", replayed_retry)

    # A different logical payment uses a different key
    other, replayed_other = store.execute("idem-PAY-ORD-201", lambda: charge(5.00))
    print("  Call 3 (different key):", other, "| replayed?", replayed_other)

    assert replayed_first is False
    assert replayed_retry is True
    assert replayed_other is False
    assert first == retry == {"charged": 99.99, "charge_id": "chg-1"}
    assert charges == [99.99, 5.00]  # 99.99 ran exactly once, despite the retry
    print("\n  ✅ Demo 4 PASSED")


def demo_5_saga_state_machine():
    """Demo 5: The saga lifecycle is a state machine with strict guarantees."""
    print("\n" + "=" * 70)
    print("DEMO 5: Saga State Machine & Compensation Guarantees")
    print("=" * 70)
    print("Story: A saga is a state machine. Success moves\n"
          "       PENDING → RUNNING → COMPLETED. A failure moves\n"
          "       RUNNING → COMPENSATING → FAILED, undoing every\n"
          "       completed step exactly once, in reverse order.\n")

    def ok_action():
        return None

    def build(ticket_ok: bool) -> OrchestratedSaga:
        # Compensations are silent here: the printed state trace below shows them.
        saga = OrchestratedSaga("saga-5", "booking")
        saga.add_step("hold_seat", ok_action, lambda: None)
        saga.add_step("charge_card", ok_action, lambda: None)
        saga.add_step(
            "issue_ticket",
            ok_action if ticket_ok else (lambda: (_ for _ in ()).throw(PaymentRejectedError("printer offline"))),
            lambda: None,
        )
        return saga

    def status_sequence(saga) -> list:
        seq = []
        for line in saga.history:
            for status in SagaStatus:
                if line.startswith(f"[{status.value}]"):
                    seq.append(status.value)
                    break
        return seq

    print("  --- Successful booking ---")
    ok_saga = build(ticket_ok=True)
    ok_saga.run()
    print("    state trace:")
    for line in ok_saga.history:
        print(f"      {line}")
    print("    sequence:", " → ".join(status_sequence(ok_saga)))
    assert status_sequence(ok_saga) == ["PENDING", "RUNNING", "COMPLETED"]

    print("\n  --- Booking that fails at the final step ---")
    fail_saga = build(ticket_ok=False)
    fail_saga.run()
    print("    state trace:")
    for line in fail_saga.history:
        print(f"      {line}")
    print("    sequence:", " → ".join(status_sequence(fail_saga)))
    assert status_sequence(fail_saga) == ["PENDING", "RUNNING", "COMPENSATING", "FAILED"]

    executed = [s.name for s in fail_saga.steps if s.executed]
    compensated_set = {s.name for s in fail_saga.steps if s.compensated}
    undo_order = [line.split("UNDO OK")[1].strip() for line in fail_saga.history if "UNDO OK" in line]
    assert executed == ["hold_seat", "charge_card"]
    assert compensated_set == {"hold_seat", "charge_card"}
    assert undo_order == ["charge_card", "hold_seat"]  # reverse execution order, each exactly once
    assert status_sequence(fail_saga).count("COMPENSATING") == 1
    print("\n  ✅ Demo 5 PASSED")


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║       P21 - DISTRIBUTED TRANSACTIONS & THE SAGA PATTERN              ║")
    print("║       Choreography | Orchestration | Outbox | Idempotency            ║")
    print("╚══════════════════════════════════════════════════════════════════════╝\n")

    demo_1_choreographed_saga()
    demo_2_orchestrated_saga()
    demo_3_transactional_outbox()
    demo_4_idempotency_keys()
    demo_5_saga_state_machine()

    print("\n" + "=" * 70)
    print("ALL 5 DEMOS PASSED ✅")
    print("=" * 70)
