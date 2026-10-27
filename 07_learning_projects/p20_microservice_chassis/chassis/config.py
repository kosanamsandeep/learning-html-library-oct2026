"""
P20 - Microservice Chassis: Configuration Management
=====================================================
Hierarchical config with environment overrides, validation, and hot-reload.
Inspired by: Spring Boot Config, 12-Factor App, Netflix Archaius.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum
import os
import json


class ConfigSource(Enum):
    """Represents ConfigSource in this learning project."""
    DEFAULT = "default"
    FILE = "file"
    ENVIRONMENT = "environment"
    OVERRIDE = "override"


@dataclass
class ConfigEntry:
    """A single configuration value with metadata."""

    key: str
    value: Any
    source: ConfigSource
    description: str = ""


class ConfigManager:
    """
    Hierarchical configuration manager.
    Priority: override > environment > file > default (highest to lowest).
    """

    def __init__(self, prefix: str = "APP"):
        """Initialize the object with the dependencies or starting values it needs."""
        self._prefix = prefix
        self._defaults: dict[str, ConfigEntry] = {}
        self._file_values: dict[str, Any] = {}
        self._overrides: dict[str, Any] = {}
        self._validators: dict[str, Callable[[Any], bool]] = {}
        self._change_listeners: list[Callable[[str, Any, Any], None]] = []

    # ── Registration ──────────────────────────────────────────
    def define(
        self,
        key: str,
        default: Any,
        description: str = "",
        validator: Callable[[Any], bool] | None = None,
    ) -> "ConfigManager":
        """Define a config key with its default value."""
        self._defaults[key] = ConfigEntry(
            key=key, value=default, source=ConfigSource.DEFAULT, description=description
        )
        if validator:
            self._validators[key] = validator
        return self

    # ── Value Resolution ──────────────────────────────────────
    def get(self, key: str, cast: type | None = None) -> Any:
        """Get config value following priority chain."""
        # 1. Overrides (highest priority)
        if key in self._overrides:
            value = self._overrides[key]
        # 2. Environment variables (PREFIX_KEY format)
        elif (
            env_key := f"{self._prefix}_{key.upper().replace('.', '_')}"
        ) and os.environ.get(env_key):
            value = os.environ[env_key]
        # 3. File values
        elif key in self._file_values:
            value = self._file_values[key]
        # 4. Defaults
        elif key in self._defaults:
            value = self._defaults[key].value
        else:
            raise KeyError(f"Unknown config key: {key}")

        if cast:
            value = cast(value)
        return value

    def get_source(self, key: str) -> ConfigSource:
        """Determine which source a value comes from."""
        env_key = f"{self._prefix}_{key.upper().replace('.', '_')}"
        if key in self._overrides:
            return ConfigSource.OVERRIDE
        elif os.environ.get(env_key):
            return ConfigSource.ENVIRONMENT
        elif key in self._file_values:
            return ConfigSource.FILE
        elif key in self._defaults:
            return ConfigSource.DEFAULT
        raise KeyError(f"Unknown config key: {key}")

    # ── Bulk Operations ───────────────────────────────────────
    def load_dict(self, values: dict[str, Any]) -> "ConfigManager":
        """Load values from a dictionary (simulates file config)."""
        self._file_values.update(values)
        return self

    def override(self, key: str, value: Any) -> "ConfigManager":
        """Set a runtime override (highest priority)."""
        if key in self._validators and not self._validators[key](value):
            raise ValueError(f"Validation failed for {key}={value}")
        old = self.get(key) if key in self._defaults else None
        self._overrides[key] = value
        for listener in self._change_listeners:
            listener(key, old, value)
        return self

    def on_change(self, listener: Callable[[str, Any, Any], None]) -> "ConfigManager":
        """Register a change listener for hot-reload notifications."""
        self._change_listeners.append(listener)
        return self

    # ── Inspection ────────────────────────────────────────────
    def all_keys(self) -> list[str]:
        """Perform the all keys step used by this project."""
        return list(self._defaults.keys())

    def snapshot(self) -> dict[str, dict]:
        """Get a snapshot of all config values with sources."""
        result = {}
        for key in self._defaults:
            result[key] = {
                "value": self.get(key),
                "source": self.get_source(key).value,
                "description": self._defaults[key].description,
            }
        return result
