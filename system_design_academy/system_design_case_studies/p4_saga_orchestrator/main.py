"""P4 Case Study · Saga Orchestrator.

A booking flow needs to: reserve a flight, reserve a hotel, charge the card.
If the card charge fails after the hotel reservation succeeded, you must undo
the hotel reservation. There is no distributed transaction in this world —
you use a *saga*: a sequence of steps, each with a compensating action.

This file shows an orchestrator that runs steps forward and, on failure,
runs the compensations in reverse order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class SagaStep:
    """One forward action + its compensating action."""

    name: str
    action: Callable[[dict], None]
    compensation: Callable[[dict], None]


@dataclass
class SagaOrchestrator:
    """Run steps forward; on failure, undo completed steps in reverse."""

    steps: list[SagaStep]
    log: list[str] = field(default_factory=list)

    def execute(self, context: dict) -> bool:
        """Return True when all steps succeed, False after a compensated rollback."""
        completed: list[SagaStep] = []
        for step in self.steps:
            try:
                self.log.append(f"-> {step.name}")
                step.action(context)
                completed.append(step)
            except (
                Exception
            ) as exc:  # noqa: BLE001 - we want to handle every failure here
                self.log.append(f"!! {step.name} failed: {exc}")
                for done in reversed(completed):
                    try:
                        done.compensation(context)
                        self.log.append(f"<- compensated {done.name}")
                    except Exception as comp_exc:  # noqa: BLE001
                        # Real systems would alert here; the saga cannot recover automatically.
                        self.log.append(
                            f"!! compensation for {done.name} failed: {comp_exc}"
                        )
                return False
        return True


# --- demo actions ----------------------------------------------------------


def reserve_flight(ctx: dict) -> None:
    """Mark a flight seat as held."""
    ctx["flight"] = "AI-202 seat 14A"


def cancel_flight(ctx: dict) -> None:
    """Release a previously held flight seat."""
    ctx.pop("flight", None)


def reserve_hotel(ctx: dict) -> None:
    """Mark a hotel room as held."""
    ctx["hotel"] = "Taj room 305"


def release_hotel(ctx: dict) -> None:
    """Release a previously held hotel room."""
    ctx.pop("hotel", None)


def charge_card(ctx: dict) -> None:
    """Pretend to charge the card — fail when the demo asks for it."""
    if ctx.get("force_payment_failure"):
        raise RuntimeError("card declined")
    ctx["charge_id"] = "ch_demo_001"


def refund_card(ctx: dict) -> None:
    """Reverse a successful charge."""
    ctx.pop("charge_id", None)


def main() -> None:
    """Run the saga twice: once successfully, once with payment failure."""
    steps = [
        SagaStep("ReserveFlight", reserve_flight, cancel_flight),
        SagaStep("ReserveHotel", reserve_hotel, release_hotel),
        SagaStep("ChargeCard", charge_card, refund_card),
    ]

    print("--- happy path ---")
    saga = SagaOrchestrator(steps=steps)
    ctx: dict = {}
    ok = saga.execute(ctx)
    print("\n".join(saga.log))
    print(f"success={ok}, final state={ctx}")

    print("\n--- payment failure path ---")
    saga = SagaOrchestrator(steps=steps)
    ctx = {"force_payment_failure": True}
    ok = saga.execute(ctx)
    print("\n".join(saga.log))
    print(f"success={ok}, final state={ctx}")


if __name__ == "__main__":
    main()
