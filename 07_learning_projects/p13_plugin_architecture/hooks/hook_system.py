"""
Hook System - The backbone of plugin architecture.
Inspired by: pytest's hookspec/hookimpl, WordPress actions/filters, tapable (webpack)

Hooks are named extension points where plugins can register callbacks.
Two types:
  - Action Hooks: Execute side effects (like WordPress do_action)
  - Filter Hooks: Transform data through a pipeline (like WordPress apply_filters)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum


class HookType(Enum):
    """Represents HookType in this learning project."""
    ACTION = "action"  # Fire-and-forget, side effects
    FILTER = "filter"  # Transform data through pipeline


@dataclass
class HookSpec:
    """Defines a hook extension point (what plugins can hook into)."""

    name: str
    hook_type: HookType
    description: str = ""


@dataclass
class HookRegistration:
    """A plugin's registration to a specific hook."""

    hook_name: str
    callback: Callable
    priority: int = 10  # Lower = earlier execution (like WordPress)
    plugin_name: str = ""


class HookRegistry:
    """
    Central registry for all hooks in the system.
    Plugins register callbacks; the core triggers hooks at extension points.

    This is the 'Mediator' between core application and plugins.
    """

    def __init__(self):
        """Initialize the object with the dependencies or starting values it needs."""
        self._specs: dict[str, HookSpec] = {}
        self._registrations: dict[str, list[HookRegistration]] = {}

    def define_hook(
        self, name: str, hook_type: HookType, description: str = ""
    ) -> None:
        """Core defines available extension points."""
        self._specs[name] = HookSpec(
            name=name, hook_type=hook_type, description=description
        )
        if name not in self._registrations:
            self._registrations[name] = []

    def register(
        self,
        hook_name: str,
        callback: Callable,
        priority: int = 10,
        plugin_name: str = "",
    ) -> None:
        """Plugin registers a callback for a hook."""
        if hook_name not in self._specs:
            raise ValueError(
                f"Unknown hook: '{hook_name}'. Available: {list(self._specs.keys())}"
            )

        registration = HookRegistration(
            hook_name=hook_name,
            callback=callback,
            priority=priority,
            plugin_name=plugin_name,
        )
        self._registrations[hook_name].append(registration)
        # Sort by priority (lower first)
        self._registrations[hook_name].sort(key=lambda r: r.priority)

    def unregister(self, hook_name: str, plugin_name: str) -> None:
        """Remove all registrations for a plugin on a hook."""
        if hook_name in self._registrations:
            self._registrations[hook_name] = [
                r
                for r in self._registrations[hook_name]
                if r.plugin_name != plugin_name
            ]

    # ─── Trigger Hooks ────────────────────────────────────────────

    def trigger_action(self, hook_name: str, **kwargs) -> list[Any]:
        """
        Trigger an ACTION hook - calls all registered callbacks.
        Returns list of results (usually ignored for actions).
        """
        self._validate_hook(hook_name, HookType.ACTION)
        results = []
        for reg in self._registrations.get(hook_name, []):
            result = reg.callback(**kwargs)
            results.append(result)
        return results

    def apply_filter(self, hook_name: str, value: Any, **kwargs) -> Any:
        """
        Trigger a FILTER hook - pipes value through all callbacks.
        Each callback receives the value and returns transformed value.
        Like a Unix pipe: value | filter1 | filter2 | filter3
        """
        self._validate_hook(hook_name, HookType.FILTER)
        for reg in self._registrations.get(hook_name, []):
            value = reg.callback(value, **kwargs)
        return value

    def _validate_hook(self, hook_name: str, expected_type: HookType) -> None:
        """Perform the validate hook step used by this project."""
        if hook_name not in self._specs:
            raise ValueError(f"Hook '{hook_name}' not defined")
        if self._specs[hook_name].hook_type != expected_type:
            raise TypeError(
                f"Hook '{hook_name}' is {self._specs[hook_name].hook_type.value}, "
                f"not {expected_type.value}"
            )

    # ─── Introspection ────────────────────────────────────────────

    def get_hooks(self) -> list[HookSpec]:
        """List all defined hooks."""
        return list(self._specs.values())

    def get_registrations(self, hook_name: str) -> list[HookRegistration]:
        """List all registrations for a hook."""
        return self._registrations.get(hook_name, [])
