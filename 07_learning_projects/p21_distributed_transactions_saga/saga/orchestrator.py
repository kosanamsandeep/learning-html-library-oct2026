"""
Orchestrated Saga
=================
A central SagaOrchestrator runs steps in order. If a step fails, every step
that already completed is compensated in strict reverse execution order.

The saga is also a state machine (only one state at a time):
    PENDING -> RUNNING -> COMPLETED
    PENDING -> RUNNING -> COMPENSATING -> FAILED

Inspired by: AWS Step Functions, NServiceBus Saga, Temporal
"""

from enum import Enum
from typing import Callable, List, Optional


class SagaStatus(Enum):
    """Lifecycle states a saga can occupy."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPENSATING = "COMPENSATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SagaStep:
    """One unit of work plus its compensating (rollback) action."""

    def __init__(
        self,
        name: str,
        action: Callable[[], None],
        compensation: Optional[Callable[[], None]] = None,
    ) -> None:
        self.name = name
        self.action = action
        self.compensation = compensation
        self.executed = False
        self.compensated = False


class OrchestratedSaga:
    """Coordinates local transactions so the whole flow either succeeds or rolls back."""

    def __init__(self, saga_id: str, name: str = "saga") -> None:
        self.saga_id = saga_id
        self.name = name
        self.steps: List[SagaStep] = []
        self.status = SagaStatus.PENDING
        self.history: List[str] = [f"[PENDING] saga '{name}' ({saga_id}) created"]
        self._completed: List[SagaStep] = []

    def add_step(
        self,
        name: str,
        action: Callable[[], None],
        compensation: Optional[Callable[[], None]] = None,
    ) -> "OrchestratedSaga":
        """Append a step (and its compensation) to the saga."""
        self.steps.append(SagaStep(name, action, compensation))
        return self

    def run(self) -> bool:
        """Execute every step; on failure compensate completed steps and return False."""
        self.status = SagaStatus.RUNNING
        self.history.append(f"[RUNNING] executing {len(self.steps)} step(s)")
        for step in self.steps:
            try:
                step.action()
            except Exception as exc:  # noqa: BLE001 - any failure starts compensation
                self.history.append(f"  STEP FAILED  {step.name}: {exc}")
                self._compensate()
                return False
            step.executed = True
            self._completed.append(step)
            self.history.append(f"  STEP OK      {step.name}")
        self.status = SagaStatus.COMPLETED
        self.history.append(f"[COMPLETED] all {len(self.steps)} step(s) succeeded")
        return True

    def _compensate(self) -> None:
        """Run compensations for completed steps in reverse execution order."""
        self.status = SagaStatus.COMPENSATING
        self.history.append(
            f"[COMPENSATING] rolling back {len(self._completed)} completed step(s) in reverse order"
        )
        for step in reversed(self._completed):
            if step.compensation is not None:
                step.compensation()
                step.compensated = True
                self.history.append(f"  UNDO OK      {step.name}")
        self.status = SagaStatus.FAILED
        self.history.append("[FAILED] saga rolled back")
