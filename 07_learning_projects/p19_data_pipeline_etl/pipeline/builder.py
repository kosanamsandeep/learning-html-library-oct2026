"""
Pipeline Builder DSL - expressive pipeline construction.
Demonstrates Builder Pattern with domain-specific language.
"""

from __future__ import annotations
from typing import Any, Callable

from pipeline.engine import (
    Pipeline,
    Stage,
    FunctionStage,
    FilterStage,
    MapStage,
    ReduceStage,
    BranchStage,
    StageConfig,
    PipelineObserver,
    LoggingObserver,
    MetricsObserver,
)
from pipeline.stages import (
    CSVParseStage,
    JSONParseStage,
    TypeCastStage,
    RenameFieldsStage,
    NormalizeStage,
    DeriveFieldStage,
    DeduplicateStage,
    ValidateStage,
    CollectStage,
    AggregateStage,
)


class PipelineBuilder:
    """
    Fluent Builder for constructing ETL pipelines.
    Provides a DSL for common ETL operations.
    """

    def __init__(self, name: str):
        """Initialize the object with the dependencies or starting values it needs."""
        self._pipeline = Pipeline(name)
        self._metrics = MetricsObserver()
        self._pipeline.observe(self._metrics)

    # ── Source / Extract ──────────────────────────────────────
    def from_csv(self, delimiter: str = ",") -> "PipelineBuilder":
        """Create an object from another representation."""
        self._pipeline.add_stage(CSVParseStage(delimiter))
        return self

    def from_json(self) -> "PipelineBuilder":
        """Create an object from another representation."""
        self._pipeline.add_stage(JSONParseStage())
        return self

    # ── Transform ─────────────────────────────────────────────
    def cast_types(self, casts: dict[str, type]) -> "PipelineBuilder":
        """Perform the cast types step used by this project."""
        self._pipeline.add_stage(TypeCastStage(casts))
        return self

    def rename(self, mapping: dict[str, str]) -> "PipelineBuilder":
        """Perform the rename step used by this project."""
        self._pipeline.add_stage(RenameFieldsStage(mapping))
        return self

    def normalize(self, fields: list[str], lowercase: bool = True) -> "PipelineBuilder":
        """Perform the normalize step used by this project."""
        self._pipeline.add_stage(NormalizeStage(fields, lowercase))
        return self

    def derive(
        self, field_name: str, compute: Callable[[dict], Any]
    ) -> "PipelineBuilder":
        """Perform the derive step used by this project."""
        self._pipeline.add_stage(DeriveFieldStage(field_name, compute))
        return self

    def deduplicate(self, key_field: str) -> "PipelineBuilder":
        """Perform the deduplicate step used by this project."""
        self._pipeline.add_stage(DeduplicateStage(key_field))
        return self

    def validate(
        self, validators: dict[str, Callable[[Any], bool]], drop_invalid: bool = True
    ) -> "PipelineBuilder":
        """Perform the validate step used by this project."""
        self._pipeline.add_stage(ValidateStage(validators, drop_invalid))
        return self

    def filter(self, name: str, predicate: Callable[[Any], bool]) -> "PipelineBuilder":
        """Perform the filter step used by this project."""
        self._pipeline.add_stage(FilterStage(name, predicate))
        return self

    def map(self, name: str, mapper: Callable[[Any], Any]) -> "PipelineBuilder":
        """Perform the map step used by this project."""
        self._pipeline.add_stage(MapStage(name, mapper))
        return self

    def reduce(
        self, name: str, reducer: Callable[[Any, Any], Any], initial: Any
    ) -> "PipelineBuilder":
        """Perform the reduce step used by this project."""
        self._pipeline.add_stage(ReduceStage(name, reducer, initial))
        return self

    def transform(
        self, name: str, fn: Callable[[Any], Any], retries: int = 0
    ) -> "PipelineBuilder":
        """Perform the transform step used by this project."""
        config = StageConfig(retries=retries)
        self._pipeline.add_stage(FunctionStage(name, fn, config))
        return self

    def branch(
        self,
        name: str,
        condition: Callable[[Any], bool],
        if_true: Stage,
        if_false: Stage,
    ) -> "PipelineBuilder":
        """Perform the branch step used by this project."""
        self._pipeline.add_stage(BranchStage(name, condition, if_true, if_false))
        return self

    # ── Load / Sink ───────────────────────────────────────────
    def collect(self) -> "PipelineBuilder":
        """Perform the collect step used by this project."""
        self._pipeline.add_stage(CollectStage())
        return self

    def aggregate(
        self, group_by: str, agg_field: str, agg_fn: Callable[[list], Any]
    ) -> "PipelineBuilder":
        """Perform the aggregate step used by this project."""
        self._pipeline.add_stage(AggregateStage(group_by, agg_field, agg_fn))
        return self

    # ── Observability ─────────────────────────────────────────
    def with_logging(self) -> "PipelineBuilder":
        """Perform the with logging step used by this project."""
        self._pipeline.observe(LoggingObserver())
        return self

    def with_observer(self, observer: PipelineObserver) -> "PipelineBuilder":
        """Perform the with observer step used by this project."""
        self._pipeline.observe(observer)
        return self

    # ── Build & Run ───────────────────────────────────────────
    def build(self) -> Pipeline:
        """Finalize and return the pipeline."""
        return self._pipeline

    @property
    def metrics(self) -> MetricsObserver:
        """Perform the metrics step used by this project."""
        return self._metrics
