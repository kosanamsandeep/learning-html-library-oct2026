"""
Plugin Base & Manager - Core plugin infrastructure.
Inspired by: pytest plugin system, Flask extensions, Sublime Text packages

Key concepts:
  - PluginMeta: Metadata about a plugin (name, version, dependencies)
  - PluginBase: ABC that all plugins must implement
  - PluginManager: Discovery, loading, dependency resolution, lifecycle
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Type

from hooks.hook_system import HookRegistry


class PluginState(Enum):
    """Represents PluginState in this learning project."""
    DISCOVERED = "discovered"
    LOADED = "loaded"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"
    ERROR = "error"


@dataclass
class PluginMeta:
    """Plugin metadata - like package.json or setup.cfg for plugins."""

    name: str
    version: str
    description: str = ""
    author: str = ""
    dependencies: list[str] = field(default_factory=list)  # Other plugin names
    provides: list[str] = field(default_factory=list)  # Capabilities this plugin offers


class PluginBase(ABC):
    """
    Abstract base class for all plugins.
    Lifecycle: discover -> load -> activate -> deactivate
    """

    def __init__(self, hook_registry: HookRegistry):
        """Initialize the object with the dependencies or starting values it needs."""
        self._hooks = hook_registry
        self._state = PluginState.DISCOVERED

    @property
    @abstractmethod
    def meta(self) -> PluginMeta:
        """Return plugin metadata."""
        ...

    @abstractmethod
    def activate(self) -> None:
        """
        Called when plugin is activated.
        Register hooks, initialize resources.
        """
        ...

    def deactivate(self) -> None:
        """Called when plugin is deactivated. Cleanup resources."""
        pass

    @property
    def state(self) -> PluginState:
        """Perform the state step used by this project."""
        return self._state


class PluginManager:
    """
    Manages the full plugin lifecycle.
    Handles: discovery, dependency resolution, loading order, activation.

    Design inspired by:
      - pytest's plugin manager (pluggy)
      - VS Code's extension host
      - Gradle's plugin resolution
    """

    def __init__(self, hook_registry: HookRegistry):
        """Initialize the object with the dependencies or starting values it needs."""
        self._hooks = hook_registry
        self._plugins: dict[str, PluginBase] = {}
        self._plugin_classes: dict[str, Type[PluginBase]] = {}
        self._activation_order: list[str] = []

    # ─── Registration ─────────────────────────────────────────────

    def register_plugin_class(self, plugin_class: Type[PluginBase]) -> None:
        """Register a plugin class for later instantiation."""
        # Instantiate temporarily to get metadata
        temp_instance = plugin_class(self._hooks)
        name = temp_instance.meta.name
        self._plugin_classes[name] = plugin_class

    def discover_and_load(self, plugin_classes: list[Type[PluginBase]]) -> list[str]:
        """
        Discover plugins, resolve dependencies, load in correct order.
        Returns list of loaded plugin names in activation order.
        """
        # Step 1: Register all plugin classes
        for cls in plugin_classes:
            self.register_plugin_class(cls)

        # Step 2: Resolve dependency order (topological sort)
        order = self._resolve_dependencies()

        # Step 3: Instantiate and activate in order
        errors = []
        for plugin_name in order:
            try:
                self._activate_plugin(plugin_name)
            except Exception as e:
                errors.append(f"{plugin_name}: {e}")

        if errors:
            print(f"  [!] Plugin errors: {errors}")

        return self._activation_order

    # ─── Dependency Resolution ────────────────────────────────────

    def _resolve_dependencies(self) -> list[str]:
        """
        Topological sort of plugins based on dependencies.
        Ensures dependencies are loaded before dependents.
        Uses Kahn's algorithm (BFS-based topological sort).
        """
        # Build adjacency and in-degree
        in_degree: dict[str, int] = {name: 0 for name in self._plugin_classes}
        graph: dict[str, list[str]] = {name: [] for name in self._plugin_classes}

        for name, cls in self._plugin_classes.items():
            temp = cls(self._hooks)
            for dep in temp.meta.dependencies:
                if dep not in self._plugin_classes:
                    raise ValueError(
                        f"Plugin '{name}' depends on '{dep}' which is not available"
                    )
                graph[dep].append(name)
                in_degree[name] += 1

        # BFS - process nodes with 0 in-degree
        queue = [name for name, degree in in_degree.items() if degree == 0]
        order = []

        while queue:
            # Sort for deterministic ordering
            queue.sort()
            node = queue.pop(0)
            order.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self._plugin_classes):
            raise ValueError("Circular dependency detected among plugins!")

        return order

    # ─── Activation ───────────────────────────────────────────────

    def _activate_plugin(self, plugin_name: str) -> None:
        """Instantiate and activate a single plugin."""
        plugin_class = self._plugin_classes[plugin_name]
        instance = plugin_class(self._hooks)
        instance.activate()
        instance._state = PluginState.ACTIVATED
        self._plugins[plugin_name] = instance
        self._activation_order.append(plugin_name)

    def deactivate_plugin(self, plugin_name: str) -> None:
        """Deactivate a plugin (reverse of activate)."""
        if plugin_name in self._plugins:
            self._plugins[plugin_name].deactivate()
            self._plugins[plugin_name]._state = PluginState.DEACTIVATED

    def deactivate_all(self) -> None:
        """Deactivate all plugins in reverse order."""
        for name in reversed(self._activation_order):
            self.deactivate_plugin(name)

    # ─── Introspection ────────────────────────────────────────────

    def get_plugin(self, name: str) -> PluginBase | None:
        """Return the requested item or information if it exists."""
        return self._plugins.get(name)

    def list_plugins(self) -> list[tuple[str, PluginState]]:
        """Return a collection of items for display or further processing."""
        return [(name, p.state) for name, p in self._plugins.items()]

    def get_activation_order(self) -> list[str]:
        """Return the requested item or information if it exists."""
        return self._activation_order.copy()
