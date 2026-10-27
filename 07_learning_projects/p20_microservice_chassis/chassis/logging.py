"""
P20 - Microservice Chassis: Structured Logging
===============================================
JSON-structured logging with correlation IDs, context propagation.
Inspired by: ELK Stack, Datadog, structlog.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from enum import IntEnum
from datetime import datetime
from contextvars import ContextVar
import json
import uuid


class LogLevel(IntEnum):
    """Represents LogLevel in this learning project."""
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    FATAL = 50


# Correlation ID propagated across async boundaries
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def set_correlation_id(cid: str | None = None) -> str:
    """Set correlation ID for current context. Generates one if not provided."""
    cid = cid or str(uuid.uuid4())[:8]
    _correlation_id.set(cid)
    return cid


def get_correlation_id() -> str:
    """Return the requested item or information if it exists."""
    return _correlation_id.get()


@dataclass
class LogEntry:
    """Structured log entry."""

    timestamp: str
    level: str
    message: str
    service: str
    correlation_id: str
    context: dict = field(default_factory=dict)

    def to_json(self) -> str:
        """Convert this object into another representation."""
        return json.dumps(
            {
                "ts": self.timestamp,
                "level": self.level,
                "msg": self.message,
                "service": self.service,
                "correlation_id": self.correlation_id,
                **self.context,
            }
        )

    def to_human(self) -> str:
        """Convert this object into another representation."""
        ctx = " ".join(f"{k}={v}" for k, v in self.context.items())
        cid = f"[{self.correlation_id}]" if self.correlation_id else ""
        return f"{self.timestamp} {self.level:5s} {cid} {self.message} {ctx}".strip()


class StructuredLogger:
    """
    Structured logger with JSON output, context binding, and level filtering.
    """

    def __init__(
        self,
        service_name: str,
        level: LogLevel = LogLevel.INFO,
        json_output: bool = False,
    ):
        """Initialize the object with the dependencies or starting values it needs."""
        self._service = service_name
        self._level = level
        self._json_output = json_output
        self._bound_context: dict[str, Any] = {}
        self._entries: list[LogEntry] = []
        self._handlers: list[Any] = []

    def bind(self, **kwargs) -> "StructuredLogger":
        """Add persistent context fields to all future log entries."""
        child = StructuredLogger(self._service, self._level, self._json_output)
        child._bound_context = {**self._bound_context, **kwargs}
        child._entries = self._entries  # Share entries list
        child._handlers = self._handlers
        return child

    def _log(self, level: LogLevel, message: str, **kwargs) -> LogEntry | None:
        """Perform the log step used by this project."""
        if level < self._level:
            return None

        entry = LogEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            level=level.name,
            message=message,
            service=self._service,
            correlation_id=get_correlation_id(),
            context={**self._bound_context, **kwargs},
        )
        self._entries.append(entry)

        output = entry.to_json() if self._json_output else entry.to_human()
        print(f"    {output}")
        return entry

    def debug(self, message: str, **kwargs) -> LogEntry | None:
        """Perform the debug step used by this project."""
        return self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> LogEntry | None:
        """Perform the info step used by this project."""
        return self._log(LogLevel.INFO, message, **kwargs)

    def warn(self, message: str, **kwargs) -> LogEntry | None:
        """Perform the warn step used by this project."""
        return self._log(LogLevel.WARN, message, **kwargs)

    def error(self, message: str, **kwargs) -> LogEntry | None:
        """Perform the error step used by this project."""
        return self._log(LogLevel.ERROR, message, **kwargs)

    def fatal(self, message: str, **kwargs) -> LogEntry | None:
        """Perform the fatal step used by this project."""
        return self._log(LogLevel.FATAL, message, **kwargs)

    @property
    def entries(self) -> list[LogEntry]:
        """Perform the entries step used by this project."""
        return list(self._entries)

    def clear(self) -> None:
        """Perform the clear step used by this project."""
        self._entries.clear()
