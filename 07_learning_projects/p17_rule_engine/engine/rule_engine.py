"""
Rule Engine Core - A generic, composable rule evaluation engine.
Inspired by: Drools (Java), Easy Rules, Specification Pattern (DDD), CLIPS

Key patterns:
  - Specification Pattern: Composable boolean predicates (AND, OR, NOT)
  - Chain of Responsibility: Rules evaluated in priority order
  - Strategy Pattern: Different rule evaluation strategies
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

# ─── Specification Pattern ────────────────────────────────────────


class Specification(ABC):
    """
    Specification Pattern - composable boolean logic.
    Used by rules to define WHEN they should fire.

    Inspired by Eric Evans' DDD Specification pattern.
    Allows building complex conditions from simple ones:
      age_spec = GreaterThan("age", 25)
      income_spec = LessThan("income", 50000)
      combined = age_spec & income_spec  # AND composition
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: dict) -> bool:
        """Check if candidate satisfies this specification."""
        ...

    @abstractmethod
    def describe(self) -> str:
        """Human-readable description of this spec."""
        ...

    def __and__(self, other: "Specification") -> "AndSpec":
        """Combine two specifications with boolean AND using the ``&`` operator.

        Example:
            ``GreaterThan("age", 18) & Equals("country", "IN")`` means
            "age must be greater than 18 AND country must be IN".
        """
        return AndSpec(self, other)

    def __or__(self, other: "Specification") -> "OrSpec":
        """Combine two specifications with boolean OR using the ``|`` operator.

        Example:
            ``Equals("tier", "gold") | GreaterThan("spend", 10000)`` means
            "the customer can qualify by tier OR by spend".
        """
        return OrSpec(self, other)

    def __invert__(self) -> "NotSpec":
        """Negate one specification with the ``~`` operator.

        Example:
            ``~Equals("status", "blocked")`` means "status must not be blocked".
        """
        return NotSpec(self)


class AndSpec(Specification):
    """Specification that passes only when both child specifications pass.

    ``left`` and ``right`` are the two smaller conditions being joined. They are
    stored separately so each one can be evaluated and described independently.
    For example, ``age > 18 AND income > 50000`` has a left side (age check) and
    a right side (income check).
    """

    def __init__(self, left: Specification, right: Specification):
        """Store the left and right specifications that must both be true."""
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: dict) -> bool:
        """Return True only when the candidate satisfies both child specs."""
        return self._left.is_satisfied_by(candidate) and self._right.is_satisfied_by(
            candidate
        )

    def describe(self) -> str:
        """Return a readable sentence fragment showing the AND relationship."""
        return f"({self._left.describe()} AND {self._right.describe()})"


class OrSpec(Specification):
    """Specification that passes when at least one child specification passes.

    ``left`` and ``right`` are simply the two alternatives. The candidate can
    satisfy the left side, the right side, or both. This is useful for rules like
    "approve if the customer is premium OR the transaction amount is small".
    """

    def __init__(self, left: Specification, right: Specification):
        """Store the two alternative specifications where either one may pass."""
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: dict) -> bool:
        """Return True when the candidate satisfies the left spec or right spec."""
        return self._left.is_satisfied_by(candidate) or self._right.is_satisfied_by(
            candidate
        )

    def describe(self) -> str:
        """Return a readable sentence fragment showing the OR relationship."""
        return f"({self._left.describe()} OR {self._right.describe()})"


class NotSpec(Specification):
    """Specification that reverses another specification's answer.

    If the wrapped specification returns True, ``NotSpec`` returns False. If the
    wrapped specification returns False, ``NotSpec`` returns True. This models
    business rules such as "customer is NOT blocked" or "order is NOT cancelled".
    """

    def __init__(self, spec: Specification):
        """Store the specification whose boolean result will be inverted."""
        self._spec = spec

    def is_satisfied_by(self, candidate: dict) -> bool:
        """Return the opposite of the wrapped specification's result."""
        return not self._spec.is_satisfied_by(candidate)

    def describe(self) -> str:
        """Return a readable sentence fragment showing the NOT relationship."""
        return f"(NOT {self._spec.describe()})"


# ─── Concrete Specifications ─────────────────────────────────────


class Equals(Specification):
    """Specification that checks whether one fact field equals an expected value."""

    def __init__(self, field: str, value: Any):
        """Store the fact field name and the value it must equal."""
        self._field = field
        self._value = value

    def is_satisfied_by(self, candidate: dict) -> bool:
        """Return True when ``candidate[field]`` equals the configured value."""
        return candidate.get(self._field) == self._value

    def describe(self) -> str:
        """Describe the equality comparison in rule-readable text."""
        return f"{self._field} == {self._value}"


class GreaterThan(Specification):
    """Specification that checks whether one numeric fact is above a threshold."""

    def __init__(self, field: str, value: float):
        """Store the fact field name and the minimum value it must exceed."""
        self._field = field
        self._value = value

    def is_satisfied_by(self, candidate: dict) -> bool:
        """Return True when ``candidate[field]`` is greater than the threshold."""
        return candidate.get(self._field, 0) > self._value

    def describe(self) -> str:
        """Describe the greater-than comparison in rule-readable text."""
        return f"{self._field} > {self._value}"


class LessThan(Specification):
    """Specification that checks whether one numeric fact is below a threshold."""

    def __init__(self, field: str, value: float):
        """Store the fact field name and the maximum value it must stay below."""
        self._field = field
        self._value = value

    def is_satisfied_by(self, candidate: dict) -> bool:
        """Return True when ``candidate[field]`` is less than the threshold."""
        return candidate.get(self._field, 0) < self._value

    def describe(self) -> str:
        """Describe the less-than comparison in rule-readable text."""
        return f"{self._field} < {self._value}"


class Between(Specification):
    """Specification that checks whether one numeric fact is inside a range."""

    def __init__(self, field: str, low: float, high: float):
        """Store the fact field name plus the inclusive lower and upper bounds."""
        self._field = field
        self._low = low
        self._high = high

    def is_satisfied_by(self, candidate: dict) -> bool:
        """Return True when ``low <= candidate[field] <= high``."""
        val = candidate.get(self._field, 0)
        return self._low <= val <= self._high

    def describe(self) -> str:
        """Describe the inclusive range comparison in rule-readable text."""
        return f"{self._low} <= {self._field} <= {self._high}"


class Contains(Specification):
    """Specification that checks whether a collection fact contains a value."""

    def __init__(self, field: str, value: Any):
        """Store the collection field name and the value that must be present."""
        self._field = field
        self._value = value

    def is_satisfied_by(self, candidate: dict) -> bool:
        """Return True when the expected value appears inside the collection."""
        collection = candidate.get(self._field, [])
        return self._value in collection

    def describe(self) -> str:
        """Describe the membership check in rule-readable text."""
        return f"{self._value} in {self._field}"


class InSet(Specification):
    """Specification that checks whether one fact value belongs to a set."""

    def __init__(self, field: str, values: set):
        """Store the fact field name and the allowed set of values."""
        self._field = field
        self._values = values

    def is_satisfied_by(self, candidate: dict) -> bool:
        """Return True when ``candidate[field]`` is one of the allowed values."""
        return candidate.get(self._field) in self._values

    def describe(self) -> str:
        """Describe the set membership check in rule-readable text."""
        return f"{self._field} in {self._values}"


# ─── Rule Definition ─────────────────────────────────────────────


@dataclass
class Rule:
    """
    A business rule: WHEN condition is met, THEN execute action.

    Components:
      - name: Human-readable identifier
      - condition: Specification that must be satisfied
      - action: What to do when rule fires
      - priority: Lower = higher priority (evaluated first)
    """

    name: str
    condition: Specification
    action: Callable[[dict, dict], None]  # (facts, results) -> None
    priority: int = 100
    description: str = ""
    group: str = "default"


@dataclass
class RuleResult:
    """Result of evaluating a single rule."""

    rule_name: str
    fired: bool
    condition_description: str
    priority: int


# ─── Rule Engine ──────────────────────────────────────────────────


class RuleEngine:
    """
    Evaluates rules against facts (input data).

    Strategies:
      - ALL: Fire all matching rules (default)
      - FIRST: Fire only the first matching rule (highest priority)
      - PRIORITY_GROUP: Fire first match in each group
    """

    def __init__(self):
        """Start with an empty, priority-sorted list of rules."""
        self._rules: list[Rule] = []

    def add_rule(self, rule: Rule) -> "RuleEngine":
        """Add a rule (fluent interface)."""
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)
        return self

    def evaluate_all(self, facts: dict) -> tuple[dict, list[RuleResult]]:
        """Fire ALL matching rules (accumulate results)."""
        results_data: dict = {}
        rule_results: list[RuleResult] = []

        for rule in self._rules:
            fired = rule.condition.is_satisfied_by(facts)
            if fired:
                rule.action(facts, results_data)
            rule_results.append(
                RuleResult(
                    rule_name=rule.name,
                    fired=fired,
                    condition_description=rule.condition.describe(),
                    priority=rule.priority,
                )
            )

        return results_data, rule_results

    def evaluate_first(self, facts: dict) -> tuple[dict, list[RuleResult]]:
        """Fire only the FIRST matching rule (highest priority wins)."""
        results_data: dict = {}
        rule_results: list[RuleResult] = []

        for rule in self._rules:
            fired = rule.condition.is_satisfied_by(facts)
            rule_results.append(
                RuleResult(
                    rule_name=rule.name,
                    fired=fired,
                    condition_description=rule.condition.describe(),
                    priority=rule.priority,
                )
            )
            if fired:
                rule.action(facts, results_data)
                break  # Stop after first match

        return results_data, rule_results

    def get_matching_rules(self, facts: dict) -> list[Rule]:
        """Get all rules whose conditions are satisfied (without firing)."""
        return [r for r in self._rules if r.condition.is_satisfied_by(facts)]

    def list_rules(self) -> list[Rule]:
        """List all registered rules."""
        return self._rules.copy()
