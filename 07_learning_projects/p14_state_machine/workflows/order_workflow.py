"""
Order Workflow - A real-world e-commerce order state machine.

States: draft -> pending_payment -> paid -> processing -> shipped -> delivered
        (with cancellation, refund, and failure paths)

Guards:
  - Can only pay if order total > 0
  - Can only ship if address is provided
  - Can only cancel before shipping
  - Refund only available after payment

This demonstrates how state machines prevent impossible business scenarios.
"""

from __future__ import annotations
from machine.fsm import StateMachine, StateConfig, Transition
from models.order import Order


def create_order_workflow(order: Order) -> StateMachine:
    """
    Factory function: creates a state machine configured for order processing.
    The order object lives in the machine's context.
    """

    context = {
        "order": order,
        "payment_attempts": 0,
        "shipped_at": None,
        "delivered_at": None,
        "cancelled_reason": None,
        "refund_amount": 0.0,
    }

    machine = StateMachine(initial_state="draft", context=context)

    # ─── Define States ────────────────────────────────────────────

    machine.add_state(
        StateConfig(
            name="draft",
            on_enter=lambda ctx: ctx["order"].add_note("Order created as draft"),
        )
    )

    machine.add_state(
        StateConfig(
            name="pending_payment",
            on_enter=lambda ctx: ctx["order"].add_note("Awaiting payment"),
        )
    )

    machine.add_state(
        StateConfig(
            name="paid",
            on_enter=lambda ctx: ctx["order"].add_note(
                f"Payment received (${ctx['order'].total_amount:.2f})"
            ),
        )
    )

    machine.add_state(
        StateConfig(
            name="processing",
            on_enter=lambda ctx: ctx["order"].add_note("Order is being prepared"),
        )
    )

    machine.add_state(
        StateConfig(
            name="shipped",
            on_enter=lambda ctx: ctx["order"].add_note(
                f"Shipped to: {ctx['order'].shipping_address}"
            ),
        )
    )

    machine.add_state(
        StateConfig(
            name="delivered",
            on_enter=lambda ctx: ctx["order"].add_note("Order delivered successfully"),
            is_final=True,
        )
    )

    machine.add_state(
        StateConfig(
            name="cancelled",
            on_enter=lambda ctx: ctx["order"].add_note(
                f"Order cancelled: {ctx.get('cancelled_reason', 'No reason')}"
            ),
            is_final=True,
        )
    )

    machine.add_state(
        StateConfig(
            name="refunded",
            on_enter=lambda ctx: ctx["order"].add_note(
                f"Refunded ${ctx['refund_amount']:.2f}"
            ),
            is_final=True,
        )
    )

    machine.add_state(
        StateConfig(
            name="payment_failed",
            on_enter=lambda ctx: ctx["order"].add_note("Payment failed"),
        )
    )

    # ─── Define Transitions with Guards ───────────────────────────

    # draft -> pending_payment (submit order)
    machine.add_transition(
        Transition(
            from_state="draft",
            event="submit",
            to_state="pending_payment",
            guard=lambda ctx: ctx["order"].total_amount > 0,
            description="Submit order for payment (requires items in cart)",
        )
    )

    # pending_payment -> paid (payment successful)
    machine.add_transition(
        Transition(
            from_state="pending_payment",
            event="pay",
            to_state="paid",
            action=lambda ctx: ctx.update(
                {"payment_attempts": ctx["payment_attempts"] + 1}
            ),
            description="Payment processed successfully",
        )
    )

    # pending_payment -> payment_failed (payment rejected)
    machine.add_transition(
        Transition(
            from_state="pending_payment",
            event="payment_fail",
            to_state="payment_failed",
            action=lambda ctx: ctx.update(
                {"payment_attempts": ctx["payment_attempts"] + 1}
            ),
            description="Payment was rejected",
        )
    )

    # payment_failed -> pending_payment (retry payment)
    machine.add_transition(
        Transition(
            from_state="payment_failed",
            event="retry_payment",
            to_state="pending_payment",
            guard=lambda ctx: ctx["payment_attempts"] < 3,
            description="Retry payment (max 3 attempts)",
        )
    )

    # payment_failed -> cancelled (too many failures)
    machine.add_transition(
        Transition(
            from_state="payment_failed",
            event="cancel",
            to_state="cancelled",
            action=lambda ctx: ctx.update(
                {"cancelled_reason": "Payment failed after max retries"}
            ),
            description="Cancel after too many payment failures",
        )
    )

    # paid -> processing (start fulfillment)
    machine.add_transition(
        Transition(
            from_state="paid",
            event="start_processing",
            to_state="processing",
            description="Begin order fulfillment",
        )
    )

    # processing -> shipped (ship the order)
    machine.add_transition(
        Transition(
            from_state="processing",
            event="ship",
            to_state="shipped",
            guard=lambda ctx: len(ctx["order"].shipping_address) > 0,
            description="Ship order (requires shipping address)",
        )
    )

    # shipped -> delivered (delivery confirmed)
    machine.add_transition(
        Transition(
            from_state="shipped",
            event="deliver",
            to_state="delivered",
            description="Delivery confirmed by customer",
        )
    )

    # Cancellation paths (only before shipping)
    for state in ["draft", "pending_payment", "paid", "processing"]:
        machine.add_transition(
            Transition(
                from_state=state,
                event="cancel",
                to_state="cancelled",
                action=lambda ctx: ctx.update(
                    {"cancelled_reason": "Customer requested cancellation"}
                ),
                description=f"Cancel from {state}",
            )
        )

    # Refund path (only after payment)
    for state in ["paid", "processing"]:
        machine.add_transition(
            Transition(
                from_state=state,
                event="refund",
                to_state="refunded",
                action=lambda ctx: ctx.update(
                    {"refund_amount": ctx["order"].total_amount}
                ),
                description=f"Full refund from {state}",
            )
        )

    # Partial refund after delivery
    machine.add_transition(
        Transition(
            from_state="delivered",
            event="refund",
            to_state="refunded",
            action=lambda ctx: ctx.update(
                {"refund_amount": ctx["order"].total_amount * 0.8}
            ),
            description="Partial refund (80%) after delivery",
        )
    )

    return machine
