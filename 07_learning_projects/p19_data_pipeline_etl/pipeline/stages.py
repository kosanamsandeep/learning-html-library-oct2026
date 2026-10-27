"""
Pre-built ETL stages for common data processing tasks.
Demonstrates real-world Extract-Transform-Load patterns.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
import json
import re

from pipeline.engine import Stage, StageConfig


# ─── Extract Stages ──────────────────────────────────────────
class CSVParseStage(Stage):
    """Extract: Parse CSV text into list of dicts."""

    def __init__(self, delimiter: str = ",", config: StageConfig | None = None):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__("csv_parse", config)
        self._delimiter = delimiter

    def process(self, data: str) -> list[dict]:
        """Perform the process step used by this project."""
        lines = data.strip().split("\n")
        if not lines:
            return []
        headers = [h.strip() for h in lines[0].split(self._delimiter)]
        rows = []
        for line in lines[1:]:
            values = [v.strip() for v in line.split(self._delimiter)]
            rows.append(dict(zip(headers, values)))
        return rows


class JSONParseStage(Stage):
    """Extract: Parse JSON string into Python objects."""

    def __init__(self, config: StageConfig | None = None):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__("json_parse", config)

    def process(self, data: str) -> Any:
        """Perform the process step used by this project."""
        return json.loads(data)


# ─── Transform Stages ────────────────────────────────────────
class TypeCastStage(Stage):
    """Transform: Cast fields to specified types."""

    def __init__(self, casts: dict[str, type], config: StageConfig | None = None):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__("type_cast", config)
        self._casts = casts

    def process(self, data: list[dict]) -> list[dict]:
        """Perform the process step used by this project."""
        result = []
        for row in data:
            new_row = dict(row)
            for field_name, cast_type in self._casts.items():
                if field_name in new_row:
                    try:
                        new_row[field_name] = cast_type(new_row[field_name])
                    except (ValueError, TypeError):
                        new_row[field_name] = None
            result.append(new_row)
        return result


class RenameFieldsStage(Stage):
    """Transform: Rename fields in records."""

    def __init__(self, mapping: dict[str, str], config: StageConfig | None = None):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__("rename_fields", config)
        self._mapping = mapping

    def process(self, data: list[dict]) -> list[dict]:
        """Perform the process step used by this project."""
        result = []
        for row in data:
            new_row = {}
            for key, value in row.items():
                new_key = self._mapping.get(key, key)
                new_row[new_key] = value
            result.append(new_row)
        return result


class NormalizeStage(Stage):
    """Transform: Normalize string fields (strip, lowercase, etc.)."""

    def __init__(
        self,
        fields: list[str],
        lowercase: bool = True,
        strip: bool = True,
        config: StageConfig | None = None,
    ):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__("normalize", config)
        self._fields = fields
        self._lowercase = lowercase
        self._strip = strip

    def process(self, data: list[dict]) -> list[dict]:
        """Perform the process step used by this project."""
        result = []
        for row in data:
            new_row = dict(row)
            for f in self._fields:
                if f in new_row and isinstance(new_row[f], str):
                    val = new_row[f]
                    if self._strip:
                        val = val.strip()
                    if self._lowercase:
                        val = val.lower()
                    new_row[f] = val
            result.append(new_row)
        return result


class DeriveFieldStage(Stage):
    """Transform: Add a derived/computed field."""

    def __init__(
        self,
        field_name: str,
        compute: Callable[[dict], Any],
        config: StageConfig | None = None,
    ):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__(f"derive_{field_name}", config)
        self._field_name = field_name
        self._compute = compute

    def process(self, data: list[dict]) -> list[dict]:
        """Perform the process step used by this project."""
        result = []
        for row in data:
            new_row = dict(row)
            new_row[self._field_name] = self._compute(row)
            result.append(new_row)
        return result


class DeduplicateStage(Stage):
    """Transform: Remove duplicate records by key field."""

    def __init__(self, key_field: str, config: StageConfig | None = None):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__("deduplicate", config)
        self._key_field = key_field

    def process(self, data: list[dict]) -> list[dict]:
        """Perform the process step used by this project."""
        seen = set()
        result = []
        for row in data:
            key = row.get(self._key_field)
            if key not in seen:
                seen.add(key)
                result.append(row)
        return result


class ValidateStage(Stage):
    """Transform: Validate records and separate valid/invalid."""

    def __init__(
        self,
        validators: dict[str, Callable[[Any], bool]],
        drop_invalid: bool = True,
        config: StageConfig | None = None,
    ):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__("validate", config)
        self._validators = validators
        self._drop_invalid = drop_invalid

    def process(self, data: list[dict]) -> list[dict]:
        """Perform the process step used by this project."""
        valid = []
        for row in data:
            is_valid = True
            for field_name, check in self._validators.items():
                if field_name in row and not check(row[field_name]):
                    is_valid = False
                    break
            if is_valid or not self._drop_invalid:
                valid.append(row)
        return valid


# ─── Load Stages ─────────────────────────────────────────────
class CollectStage(Stage):
    """Load: Collect results into a summary dict."""

    def __init__(self, config: StageConfig | None = None):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__("collect", config)

    def process(self, data: list[dict]) -> dict:
        """Perform the process step used by this project."""
        return {
            "record_count": len(data),
            "records": data,
            "fields": list(data[0].keys()) if data else [],
        }


class AggregateStage(Stage):
    """Load: Aggregate records by a group field."""

    def __init__(
        self,
        group_by: str,
        agg_field: str,
        agg_fn: Callable[[list], Any],
        config: StageConfig | None = None,
    ):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__(f"aggregate_by_{group_by}", config)
        self._group_by = group_by
        self._agg_field = agg_field
        self._agg_fn = agg_fn

    def process(self, data: list[dict]) -> dict[str, Any]:
        """Perform the process step used by this project."""
        groups: dict[str, list] = {}
        for row in data:
            key = str(row.get(self._group_by, "unknown"))
            groups.setdefault(key, []).append(row.get(self._agg_field))
        return {k: self._agg_fn(v) for k, v in groups.items()}
