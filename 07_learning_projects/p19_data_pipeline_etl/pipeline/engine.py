"""
P19 - Data Pipeline ETL Framework
==================================
Pipeline Pattern + Builder Pattern + Observers + Middleware

Inspired by Apache Beam / Luigi / Prefect pipeline architectures.
Each pipeline is a DAG of stages with type-safe connections,
retry logic, and observable execution events.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar
from enum import Enum
from datetime import datetime
import time
import uuid

T = TypeVar("T")
U = TypeVar("U")


# ─── Stage Status ─────────────────────────────────────────────
class StageStatus(Enum):
    """Represents StageStatus in this learning project."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result of a single stage execution."""

    stage_name: str
    status: StageStatus
    output: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    started_at: datetime | None = None
    finished_at: datetime | None = None


# ─── Pipeline Events (Observer Pattern) ──────────────────────
class PipelineEvent(Enum):
    """Represents something important that already happened in the system."""

    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    STAGE_FAILED = "stage_failed"
    STAGE_RETRYING = "stage_retrying"


@dataclass
class EventPayload:
    """Represents something important that already happened in the system."""

    event: PipelineEvent
    pipeline_id: str
    stage_name: str | None = None
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class PipelineObserver(ABC):
    """Observer that receives pipeline execution events."""

    @abstractmethod
    def on_event(self, payload: EventPayload) -> None:
        """React to one pipeline event emitted by the engine."""
        ...


class LoggingObserver(PipelineObserver):
    """Logs all pipeline events to console."""

    def __init__(self):
        """Initialize the object with the dependencies or starting values it needs."""
        self.events: list[EventPayload] = []

    def on_event(self, payload: EventPayload) -> None:
        """Perform the on event step used by this project."""
        self.events.append(payload)
        icon = {
            PipelineEvent.PIPELINE_STARTED: "🚀",
            PipelineEvent.PIPELINE_COMPLETED: "✅",
            PipelineEvent.PIPELINE_FAILED: "💥",
            PipelineEvent.STAGE_STARTED: "▶️",
            PipelineEvent.STAGE_COMPLETED: "✔️",
            PipelineEvent.STAGE_FAILED: "❌",
            PipelineEvent.STAGE_RETRYING: "🔄",
        }.get(payload.event, "📌")
        stage_info = f" [{payload.stage_name}]" if payload.stage_name else ""
        print(f"  {icon} {payload.event.value}{stage_info} {payload.data}")


class MetricsObserver(PipelineObserver):
    """Collects execution metrics."""

    def __init__(self):
        """Initialize the object with the dependencies or starting values it needs."""
        self.stage_durations: dict[str, float] = {}
        self.total_duration: float = 0.0
        self.retry_count: int = 0

    def on_event(self, payload: EventPayload) -> None:
        """Perform the on event step used by this project."""
        if payload.event == PipelineEvent.STAGE_COMPLETED:
            duration = payload.data.get("duration_ms", 0)
            self.stage_durations[payload.stage_name or "unknown"] = duration
            self.total_duration += duration
        elif payload.event == PipelineEvent.STAGE_RETRYING:
            self.retry_count += 1


# ─── Stage (Abstract base) ───────────────────────────────────
@dataclass
class StageConfig:
    """Configuration for stage execution behavior."""

    retries: int = 0
    retry_delay_ms: float = 100.0
    timeout_ms: float | None = None
    skip_on_failure: bool = False


class Stage(ABC):
    """Base class for all pipeline stages."""

    def __init__(self, name: str, config: StageConfig | None = None):
        """Initialize the object with the dependencies or starting values it needs."""
        self.name = name
        self.config = config or StageConfig()

    @abstractmethod
    def process(self, data: Any) -> Any:
        """Transform input data and return output."""
        ...

    def validate_input(self, data: Any) -> bool:
        """Optional input validation. Override to add checks."""
        return True


class FunctionStage(Stage):
    """Stage wrapping a plain function (for quick definitions)."""

    def __init__(
        self, name: str, fn: Callable[[Any], Any], config: StageConfig | None = None
    ):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__(name, config)
        self._fn = fn

    def process(self, data: Any) -> Any:
        """Perform the process step used by this project."""
        return self._fn(data)


class FilterStage(Stage):
    """Stage that filters items from a collection."""

    def __init__(
        self,
        name: str,
        predicate: Callable[[Any], bool],
        config: StageConfig | None = None,
    ):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__(name, config)
        self._predicate = predicate

    def process(self, data: list) -> list:
        """Perform the process step used by this project."""
        return [item for item in data if self._predicate(item)]


class MapStage(Stage):
    """Stage that maps a function over a collection (Map step of MapReduce)."""

    def __init__(
        self, name: str, mapper: Callable[[Any], Any], config: StageConfig | None = None
    ):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__(name, config)
        self._mapper = mapper

    def process(self, data: list) -> list:
        """Perform the process step used by this project."""
        return [self._mapper(item) for item in data]


class ReduceStage(Stage):
    """Stage that reduces a collection to a single value."""

    def __init__(
        self,
        name: str,
        reducer: Callable[[Any, Any], Any],
        initial: Any,
        config: StageConfig | None = None,
    ):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__(name, config)
        self._reducer = reducer
        self._initial = initial

    def process(self, data: list) -> Any:
        """Perform the process step used by this project."""
        result = self._initial
        for item in data:
            result = self._reducer(result, item)
        return result


class BranchStage(Stage):
    """Conditional branching - routes data to different sub-stages."""

    def __init__(
        self,
        name: str,
        condition: Callable[[Any], bool],
        if_true: Stage,
        if_false: Stage,
    ):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__(name)
        self._condition = condition
        self._if_true = if_true
        self._if_false = if_false

    def process(self, data: Any) -> Any:
        """Perform the process step used by this project."""
        if self._condition(data):
            return self._if_true.process(data)
        return self._if_false.process(data)


# ─── Pipeline (Builder Pattern) ──────────────────────────────
class Pipeline:
    """
    A composable data pipeline built with the Builder Pattern.
    Stages execute sequentially, each receiving the output of the previous.
    """

    def __init__(self, name: str):
        """Initialize the object with the dependencies or starting values it needs."""
        self.name = name
        self.pipeline_id = str(uuid.uuid4())[:8]
        self._stages: list[Stage] = []
        self._observers: list[PipelineObserver] = []
        self._results: list[StageResult] = []
        self._middleware: list[Callable] = []

    # ── Builder Methods (fluent API) ──────────────────────────
    def add_stage(self, stage: Stage) -> "Pipeline":
        """Add a stage to the pipeline. Returns self for chaining."""
        self._stages.append(stage)
        return self

    def add_function(
        self, name: str, fn: Callable[[Any], Any], retries: int = 0
    ) -> "Pipeline":
        """Shortcut: add a function as a stage."""
        config = StageConfig(retries=retries)
        self._stages.append(FunctionStage(name, fn, config))
        return self

    def add_filter(self, name: str, predicate: Callable[[Any], bool]) -> "Pipeline":
        """Shortcut: add a filter stage."""
        self._stages.append(FilterStage(name, predicate))
        return self

    def add_map(self, name: str, mapper: Callable[[Any], Any]) -> "Pipeline":
        """Shortcut: add a map stage."""
        self._stages.append(MapStage(name, mapper))
        return self

    def add_reduce(
        self, name: str, reducer: Callable[[Any, Any], Any], initial: Any
    ) -> "Pipeline":
        """Shortcut: add a reduce stage."""
        self._stages.append(ReduceStage(name, reducer, initial))
        return self

    def observe(self, observer: PipelineObserver) -> "Pipeline":
        """Attach an observer. Returns self for chaining."""
        self._observers.append(observer)
        return self

    # ── Execution Engine ──────────────────────────────────────
    def _emit(
        self,
        event: PipelineEvent,
        stage_name: str | None = None,
        data: dict | None = None,
    ) -> None:
        """Perform the emit step used by this project."""
        payload = EventPayload(
            event=event,
            pipeline_id=self.pipeline_id,
            stage_name=stage_name,
            data=data or {},
        )
        for obs in self._observers:
            obs.on_event(payload)

    def _execute_stage(self, stage: Stage, data: Any) -> StageResult:
        """Execute a single stage with retry logic."""
        attempts = 0
        max_attempts = stage.config.retries + 1

        while attempts < max_attempts:
            attempts += 1
            started = datetime.now()
            start_time = time.perf_counter()

            try:
                if not stage.validate_input(data):
                    raise ValueError(
                        f"Input validation failed for stage '{stage.name}'"
                    )

                output = stage.process(data)
                elapsed = (time.perf_counter() - start_time) * 1000

                return StageResult(
                    stage_name=stage.name,
                    status=StageStatus.SUCCESS,
                    output=output,
                    duration_ms=elapsed,
                    started_at=started,
                    finished_at=datetime.now(),
                )
            except Exception as e:
                elapsed = (time.perf_counter() - start_time) * 1000
                if attempts < max_attempts:
                    self._emit(
                        PipelineEvent.STAGE_RETRYING,
                        stage.name,
                        {"attempt": attempts, "error": str(e)},
                    )
                    time.sleep(stage.config.retry_delay_ms / 1000)
                else:
                    return StageResult(
                        stage_name=stage.name,
                        status=StageStatus.FAILED,
                        error=str(e),
                        duration_ms=elapsed,
                        started_at=started,
                        finished_at=datetime.now(),
                    )

        # Should not reach here, but safety fallback
        return StageResult(
            stage_name=stage.name, status=StageStatus.FAILED, error="Unknown error"
        )

    def run(self, initial_data: Any) -> "PipelineResult":
        """Execute the entire pipeline."""
        self._results = []
        self._emit(
            PipelineEvent.PIPELINE_STARTED,
            data={"input_type": type(initial_data).__name__},
        )

        current_data = initial_data

        for stage in self._stages:
            self._emit(PipelineEvent.STAGE_STARTED, stage.name)

            result = self._execute_stage(stage, current_data)
            self._results.append(result)

            if result.status == StageStatus.SUCCESS:
                self._emit(
                    PipelineEvent.STAGE_COMPLETED,
                    stage.name,
                    {"duration_ms": round(result.duration_ms, 2)},
                )
                current_data = result.output
            else:
                self._emit(
                    PipelineEvent.STAGE_FAILED, stage.name, {"error": result.error}
                )
                if stage.config.skip_on_failure:
                    result.status = StageStatus.SKIPPED
                    continue
                self._emit(
                    PipelineEvent.PIPELINE_FAILED, data={"failed_stage": stage.name}
                )
                return PipelineResult(
                    pipeline_name=self.name,
                    pipeline_id=self.pipeline_id,
                    success=False,
                    output=None,
                    stage_results=self._results,
                )

        self._emit(
            PipelineEvent.PIPELINE_COMPLETED, data={"stages_run": len(self._results)}
        )

        return PipelineResult(
            pipeline_name=self.name,
            pipeline_id=self.pipeline_id,
            success=True,
            output=current_data,
            stage_results=self._results,
        )


@dataclass
class PipelineResult:
    """Final result of a pipeline execution."""

    pipeline_name: str
    pipeline_id: str
    success: bool
    output: Any
    stage_results: list[StageResult]

    @property
    def total_duration_ms(self) -> float:
        """Perform the total duration ms step used by this project."""
        return sum(r.duration_ms for r in self.stage_results)

    @property
    def failed_stage(self) -> str | None:
        """Perform the failed stage step used by this project."""
        for r in self.stage_results:
            if r.status == StageStatus.FAILED:
                return r.stage_name
        return None

    def summary(self) -> str:
        """Perform the summary step used by this project."""
        lines = [
            f"Pipeline: {self.pipeline_name} ({'SUCCESS' if self.success else 'FAILED'})"
        ]
        lines.append(f"Total Duration: {self.total_duration_ms:.1f}ms")
        for r in self.stage_results:
            icon = (
                "✔️"
                if r.status == StageStatus.SUCCESS
                else "❌" if r.status == StageStatus.FAILED else "⏭️"
            )
            lines.append(
                f"  {icon} {r.stage_name}: {r.status.value} ({r.duration_ms:.1f}ms)"
            )
        return "\n".join(lines)
