"""
P20 - Microservice Chassis: Lifecycle Manager
==============================================
Graceful startup/shutdown with dependency ordering and hook system.
Inspired by: Spring ApplicationContext, Go service frameworks.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum
from datetime import datetime
import time


class LifecyclePhase(Enum):
    """Represents LifecyclePhase in this learning project."""

    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass
class ComponentInfo:
    """Registration info for a lifecycle-managed component."""

    name: str
    component: "LifecycleComponent"
    priority: int = 0  # Lower starts first, stops last
    dependencies: list[str] = field(default_factory=list)


class LifecycleComponent(ABC):
    """Base class for components with lifecycle management."""

    @abstractmethod
    def start(self) -> None:
        """Initialize the component."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Gracefully shut down the component."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the component name shown in lifecycle logs."""
        ...


class LifecycleManager:
    """
    Manages orderly startup and shutdown of service components.
    Components start in priority order (low first) and stop in reverse.
    """

    def __init__(self, service_name: str):
        """Initialize the object with the dependencies or starting values it needs."""
        self.service_name = service_name
        self._components: list[ComponentInfo] = []
        self._phase = LifecyclePhase.CREATED
        self._started_components: list[ComponentInfo] = []
        self._hooks: dict[LifecyclePhase, list[Callable]] = {
            p: [] for p in LifecyclePhase
        }
        self._start_time: float | None = None
        self._errors: list[tuple[str, Exception]] = []

    @property
    def phase(self) -> LifecyclePhase:
        """Perform the phase step used by this project."""
        return self._phase

    @property
    def uptime_seconds(self) -> float:
        """Perform the uptime seconds step used by this project."""
        if self._start_time:
            return time.time() - self._start_time
        return 0.0

    def register(
        self,
        component: LifecycleComponent,
        priority: int = 0,
        dependencies: list[str] | None = None,
    ) -> "LifecycleManager":
        """Register a component for lifecycle management."""
        info = ComponentInfo(
            name=component.name,
            component=component,
            priority=priority,
            dependencies=dependencies or [],
        )
        self._components.append(info)
        return self

    def on(self, phase: LifecyclePhase, hook: Callable) -> "LifecycleManager":
        """Register a hook for a lifecycle phase."""
        self._hooks[phase].append(hook)
        return self

    def _run_hooks(self, phase: LifecyclePhase) -> None:
        """Perform the run hooks step used by this project."""
        for hook in self._hooks[phase]:
            hook()

    def start(self) -> bool:
        """Start all components in priority order."""
        self._phase = LifecyclePhase.STARTING
        self._run_hooks(LifecyclePhase.STARTING)
        self._start_time = time.time()

        # Sort by priority (lower = start first)
        ordered = sorted(self._components, key=lambda c: c.priority)

        for info in ordered:
            try:
                info.component.start()
                self._started_components.append(info)
            except Exception as e:
                self._errors.append((info.name, e))
                self._phase = LifecyclePhase.FAILED
                self._run_hooks(LifecyclePhase.FAILED)
                # Stop already-started components in reverse
                self._stop_started()
                return False

        self._phase = LifecyclePhase.RUNNING
        self._run_hooks(LifecyclePhase.RUNNING)
        return True

    def stop(self) -> bool:
        """Gracefully stop all components in reverse priority order."""
        self._phase = LifecyclePhase.STOPPING
        self._run_hooks(LifecyclePhase.STOPPING)
        self._stop_started()
        self._phase = LifecyclePhase.STOPPED
        self._run_hooks(LifecyclePhase.STOPPED)
        return len(self._errors) == 0

    def _stop_started(self) -> None:
        """Stop components in reverse order."""
        for info in reversed(self._started_components):
            try:
                info.component.stop()
            except Exception as e:
                self._errors.append((info.name, e))
        self._started_components.clear()

    def status(self) -> dict:
        """Get current lifecycle status."""
        return {
            "service": self.service_name,
            "phase": self._phase.value,
            "uptime_s": round(self.uptime_seconds, 2),
            "components": [c.name for c in self._components],
            "started": [c.name for c in self._started_components],
            "errors": [(name, str(e)) for name, e in self._errors],
        }
