"""
Finite State Machine Engine - Generic, reusable FSM implementation.
Inspired by: XState (JS), django-fsm, Spring Statemachine, Erlang gen_statem

Key concepts:
  - State: A named condition the entity is in
  - Transition: A rule for moving between states
  - Event: What triggers a transition
  - Guard: A condition that must be true for transition to fire
  - Action: Side effect executed during transition (on_enter, on_exit, on_transition)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum


@dataclass
class Transition:
    """
    A single transition rule in the state machine.
    
    from_state --[event]--> to_state  (if guard passes)
    """
    from_state: str
    event: str
    to_state: str
    guard: Callable[[dict], bool] | None = None      # Condition to check
    action: Callable[[dict], None] | None = None     # Side effect on transition
    description: str = ""


@dataclass
class StateConfig:
    """Configuration for a single state."""
    name: str
    on_enter: Callable[[dict], None] | None = None   # Called when entering state
    on_exit: Callable[[dict], None] | None = None    # Called when leaving state
    is_final: bool = False                            # Terminal state (no outgoing transitions)


@dataclass
class TransitionResult:
    """Result of attempting a transition."""
    success: bool
    from_state: str
    to_state: str | None = None
    event: str = ""
    error: str = ""
    guard_failed: bool = False


class StateMachine:
    """
    A generic Finite State Machine engine.
    
    Features:
      - Guard conditions (prevent invalid transitions)
      - Entry/Exit actions per state
      - Transition actions (side effects)
      - Event history / audit trail
      - Context (shared mutable data across the machine)
    
    Usage:
        machine = StateMachine(initial_state="idle")
        machine.add_state(StateConfig(name="idle"))
        machine.add_transition(Transition(from_state="idle", event="start", to_state="running"))
        machine.send("start")  # Transitions to "running"
    """

    def __init__(self, initial_state: str, context: dict | None = None):
        """Initialize the object with the dependencies or starting values it needs."""
        self._current_state: str = initial_state
        self._states: dict[str, StateConfig] = {}
        self._transitions: list[Transition] = []
        self._context: dict = context or {}
        self._history: list[TransitionResult] = []
        self._listeners: list[Callable[[TransitionResult], None]] = []

    # ─── Configuration ────────────────────────────────────────────

    def add_state(self, config: StateConfig) -> "StateMachine":
        """Add a state configuration (fluent interface)."""
        self._states[config.name] = config
        return self

    def add_transition(self, transition: Transition) -> "StateMachine":
        """Add a transition rule (fluent interface)."""
        self._transitions.append(transition)
        return self

    def on_transition(self, listener: Callable[[TransitionResult], None]) -> None:
        """Register a listener for all transitions (Observer pattern)."""
        self._listeners.append(listener)

    # ─── Core Operations ──────────────────────────────────────────

    @property
    def current_state(self) -> str:
        """Perform the current state step used by this project."""
        return self._current_state

    @property
    def context(self) -> dict:
        """Perform the context step used by this project."""
        return self._context

    @property
    def history(self) -> list[TransitionResult]:
        """Perform the history step used by this project."""
        return self._history.copy()

    def can_send(self, event: str) -> bool:
        """Check if an event can trigger a transition from current state."""
        for t in self._transitions:
            if t.from_state == self._current_state and t.event == event:
                if t.guard is None or t.guard(self._context):
                    return True
        return False

    def available_events(self) -> list[str]:
        """List events that can be sent from current state."""
        events = []
        for t in self._transitions:
            if t.from_state == self._current_state:
                if t.guard is None or t.guard(self._context):
                    events.append(t.event)
        return events

    def send(self, event: str) -> TransitionResult:
        """
        Send an event to the machine. If a valid transition exists
        and guards pass, perform the transition.
        """
        # Find matching transition
        matching = [
            t for t in self._transitions
            if t.from_state == self._current_state and t.event == event
        ]

        if not matching:
            result = TransitionResult(
                success=False,
                from_state=self._current_state,
                event=event,
                error=f"No transition for event '{event}' in state '{self._current_state}'"
            )
            self._history.append(result)
            return result

        # Try transitions in order (first valid one wins)
        for transition in matching:
            # Check guard
            if transition.guard and not transition.guard(self._context):
                continue  # Guard failed, try next matching transition

            # Perform transition
            old_state = self._current_state

            # 1. Exit action on old state
            if old_state in self._states and self._states[old_state].on_exit:
                self._states[old_state].on_exit(self._context)

            # 2. Transition action
            if transition.action:
                transition.action(self._context)

            # 3. Update state
            self._current_state = transition.to_state

            # 4. Enter action on new state
            if transition.to_state in self._states and self._states[transition.to_state].on_enter:
                self._states[transition.to_state].on_enter(self._context)

            # Record result
            result = TransitionResult(
                success=True,
                from_state=old_state,
                to_state=transition.to_state,
                event=event,
            )
            self._history.append(result)

            # Notify listeners
            for listener in self._listeners:
                listener(result)

            return result

        # All guards failed
        result = TransitionResult(
            success=False,
            from_state=self._current_state,
            event=event,
            error=f"All guards failed for event '{event}' in state '{self._current_state}'",
            guard_failed=True,
        )
        self._history.append(result)
        return result

    def is_in_final_state(self) -> bool:
        """Check if machine is in a terminal state."""
        if self._current_state in self._states:
            return self._states[self._current_state].is_final
        return False

    def reset(self, initial_state: str, context: dict | None = None) -> None:
        """Reset machine to a new initial state."""
        self._current_state = initial_state
        self._context = context or {}
        self._history.clear()
