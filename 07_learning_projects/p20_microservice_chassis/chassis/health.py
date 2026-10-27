"""
P20 - Microservice Chassis: Health Checks
==========================================
Liveness/Readiness probes with composable health indicators.
Inspired by: Spring Boot Actuator, Kubernetes probes, Consul.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum
from datetime import datetime
import time


class HealthStatus(Enum):
    """Represents HealthStatus in this learning project."""

    UP = "UP"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


@dataclass
class HealthDetail:
    """Result of a single health check."""

    name: str
    status: HealthStatus
    details: dict = field(default_factory=dict)
    duration_ms: float = 0.0
    checked_at: str = ""


@dataclass
class HealthReport:
    """Aggregate health report for the service."""

    status: HealthStatus
    checks: list[HealthDetail]
    service_name: str
    uptime_seconds: float

    def to_dict(self) -> dict:
        """Convert this object into another representation."""
        return {
            "status": self.status.value,
            "service": self.service_name,
            "uptime_s": round(self.uptime_seconds, 1),
            "checks": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "duration_ms": round(c.duration_ms, 2),
                    **c.details,
                }
                for c in self.checks
            ],
        }


class HealthIndicator(ABC):
    """Base class for health check indicators."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the display name used for this health indicator."""
        ...

    @abstractmethod
    def check(self) -> HealthDetail:
        """Run the health check and return a detailed status object."""
        ...


class FunctionHealthIndicator(HealthIndicator):
    """Health indicator wrapping a callable."""

    def __init__(self, name: str, check_fn: Callable[[], dict]):
        """Initialize the object with the dependencies or starting values it needs."""
        self._name = name
        self._check_fn = check_fn

    @property
    def name(self) -> str:
        """Perform the name step used by this project."""
        return self._name

    def check(self) -> HealthDetail:
        """Perform the check step used by this project."""
        start = time.perf_counter()
        try:
            result = self._check_fn()
            elapsed = (time.perf_counter() - start) * 1000
            status = (
                HealthStatus.UP if result.get("healthy", True) else HealthStatus.DOWN
            )
            return HealthDetail(
                name=self._name,
                status=status,
                details=result,
                duration_ms=elapsed,
                checked_at=datetime.now().isoformat(),
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return HealthDetail(
                name=self._name,
                status=HealthStatus.DOWN,
                details={"error": str(e)},
                duration_ms=elapsed,
                checked_at=datetime.now().isoformat(),
            )


class HealthRegistry:
    """
    Registry of health indicators with liveness/readiness separation.

    - Liveness: Is the process alive? (restart if failing)
    - Readiness: Can it serve traffic? (remove from LB if failing)
    """

    def __init__(self, service_name: str):
        """Initialize the object with the dependencies or starting values it needs."""
        self._service_name = service_name
        self._liveness: list[HealthIndicator] = []
        self._readiness: list[HealthIndicator] = []
        self._start_time = time.time()

    def register_liveness(self, indicator: HealthIndicator) -> "HealthRegistry":
        """Perform the register liveness step used by this project."""
        self._liveness.append(indicator)
        return self

    def register_readiness(self, indicator: HealthIndicator) -> "HealthRegistry":
        """Perform the register readiness step used by this project."""
        self._readiness.append(indicator)
        return self

    def register(
        self, indicator: HealthIndicator, liveness: bool = False, readiness: bool = True
    ) -> "HealthRegistry":
        """Register an indicator for liveness, readiness, or both."""
        if liveness:
            self._liveness.append(indicator)
        if readiness:
            self._readiness.append(indicator)
        return self

    def _run_checks(self, indicators: list[HealthIndicator]) -> HealthReport:
        """Perform the run checks step used by this project."""
        checks = [ind.check() for ind in indicators]
        # Overall status: DOWN if any DOWN, DEGRADED if any DEGRADED
        if any(c.status == HealthStatus.DOWN for c in checks):
            overall = HealthStatus.DOWN
        elif any(c.status == HealthStatus.DEGRADED for c in checks):
            overall = HealthStatus.DEGRADED
        elif checks:
            overall = HealthStatus.UP
        else:
            overall = HealthStatus.UNKNOWN

        return HealthReport(
            status=overall,
            checks=checks,
            service_name=self._service_name,
            uptime_seconds=time.time() - self._start_time,
        )

    def liveness(self) -> HealthReport:
        """Run liveness checks."""
        return self._run_checks(self._liveness)

    def readiness(self) -> HealthReport:
        """Run readiness checks."""
        return self._run_checks(self._readiness)

    def full(self) -> HealthReport:
        """Run all registered checks."""
        all_indicators = list(
            {id(i): i for i in self._liveness + self._readiness}.values()
        )
        return self._run_checks(all_indicators)
