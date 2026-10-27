"""
P19 - Data Pipeline ETL Framework
==================================
5 Demos showing Pipeline Pattern, Builder Pattern, MapReduce, and Observers.

Inspired by: Apache Beam, Luigi, Prefect, dbt
Patterns: Pipeline, Builder, Observer, MapReduce, Strategy
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

from pipeline.engine import (
    Pipeline,
    FunctionStage,
    FilterStage,
    MapStage,
    ReduceStage,
    StageConfig,
    LoggingObserver,
    MetricsObserver,
    PipelineResult,
)
from pipeline.stages import (
    CSVParseStage,
    TypeCastStage,
    NormalizeStage,
    DeriveFieldStage,
    DeduplicateStage,
    ValidateStage,
    AggregateStage,
    CollectStage,
)
from pipeline.builder import PipelineBuilder


def demo_1_basic_csv_pipeline():
    """Demo 1: Basic CSV ETL pipeline with type casting and validation."""
    print("=" * 70)
    print("DEMO 1: Basic CSV ETL Pipeline")
    print("=" * 70)
    print("Story: Process employee salary data from CSV, clean and validate.\n")

    csv_data = """name,department,salary,age
Alice,Engineering,95000,32
Bob,Marketing,72000,28
Charlie,Engineering,110000,45
Diana,Sales,68000,25
Eve,Engineering,125000,38
Frank,Marketing,71000,55
Grace,Sales,82000,30
Hank,Engineering,99000,27"""

    # Build pipeline using fluent builder
    builder = PipelineBuilder("Employee ETL")
    pipeline = (
        builder.from_csv()
        .cast_types({"salary": int, "age": int})
        .normalize(["department"], lowercase=True)
        .validate(
            {
                "salary": lambda s: s is not None and s > 0,
                "age": lambda a: a is not None and 18 <= a <= 70,
            }
        )
        .derive("tax_bracket", lambda r: "high" if r["salary"] > 100000 else "standard")
        .derive(
            "seniority",
            lambda r: (
                "senior" if r["age"] > 35 else "mid" if r["age"] > 28 else "junior"
            ),
        )
        .collect()
        .build()
    )

    result = pipeline.run(csv_data)

    print(f"  Pipeline: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"  Records processed: {result.output['record_count']}")
    print(f"  Fields: {result.output['fields']}")
    print(f"  Total duration: {result.total_duration_ms:.2f}ms")
    print("\n  Sample records:")
    for rec in result.output["records"][:3]:
        print(
            f"    {rec['name']}: ${rec['salary']:,} | {rec['tax_bracket']} | {rec['seniority']}"
        )

    assert result.success
    assert result.output["record_count"] == 8
    print("\n  ✅ Demo 1 PASSED")


def demo_2_mapreduce_aggregation():
    """Demo 2: MapReduce pattern - map sales data then reduce to totals."""
    print("\n" + "=" * 70)
    print("DEMO 2: MapReduce Aggregation Pipeline")
    print("=" * 70)
    print("Story: Aggregate sales data by region using Map-Reduce.\n")

    sales_data = [
        {"product": "Widget A", "region": "North", "amount": 1200},
        {"product": "Widget B", "region": "South", "amount": 800},
        {"product": "Widget A", "region": "North", "amount": 1500},
        {"product": "Widget C", "region": "East", "amount": 2200},
        {"product": "Widget B", "region": "South", "amount": 950},
        {"product": "Widget A", "region": "East", "amount": 1800},
        {"product": "Widget C", "region": "North", "amount": 3100},
        {"product": "Widget B", "region": "West", "amount": 670},
        {"product": "Widget A", "region": "West", "amount": 1400},
        {"product": "Widget C", "region": "South", "amount": 2500},
    ]

    # Pipeline 1: Total by region
    region_pipeline = Pipeline("Sales by Region").add_stage(
        AggregateStage("region", "amount", sum)
    )
    region_result = region_pipeline.run(sales_data)

    print("  Sales by Region:")
    for region, total in sorted(region_result.output.items()):
        print(f"    {region}: ${total:,}")

    # Pipeline 2: MapReduce - apply discount then sum
    mapreduce_pipeline = (
        Pipeline("MapReduce Discounted Sales")
        .add_stage(
            MapStage(
                "apply_10pct_discount",
                lambda row: {**row, "discounted": int(row["amount"] * 0.9)},
            )
        )
        .add_stage(
            ReduceStage("sum_discounted", lambda acc, row: acc + row["discounted"], 0)
        )
    )
    mr_result = mapreduce_pipeline.run(sales_data)

    total_original = sum(s["amount"] for s in sales_data)
    print(f"\n  Original total:   ${total_original:,}")
    print(f"  After 10% discount: ${mr_result.output:,}")
    print(f"  Savings:            ${total_original - mr_result.output:,}")

    assert region_result.success
    assert mr_result.success
    assert mr_result.output == int(total_original * 0.9)
    print("\n  ✅ Demo 2 PASSED")


def demo_3_pipeline_with_observers():
    """Demo 3: Observable pipeline with logging and metrics collection."""
    print("\n" + "=" * 70)
    print("DEMO 3: Observable Pipeline (Logging + Metrics)")
    print("=" * 70)
    print("Story: Monitor pipeline execution with real-time observers.\n")

    data = list(range(1, 101))  # Numbers 1-100

    logger = LoggingObserver()
    metrics = MetricsObserver()

    pipeline = (
        Pipeline("Number Cruncher")
        .add_stage(FilterStage("filter_even", lambda x: x % 2 == 0))
        .add_stage(MapStage("square", lambda x: x**2))
        .add_stage(FilterStage("filter_gt_1000", lambda x: x > 1000))
        .add_stage(ReduceStage("sum_all", lambda acc, x: acc + x, 0))
    )
    pipeline.observe(logger)
    pipeline.observe(metrics)

    result = pipeline.run(data)

    print(f"\n  Final result: {result.output:,}")
    print(f"\n  Metrics collected:")
    print(f"    Total duration: {metrics.total_duration:.2f}ms")
    print(f"    Retries: {metrics.retry_count}")
    print(f"    Stage durations:")
    for stage, dur in metrics.stage_durations.items():
        print(f"      {stage}: {dur:.2f}ms")
    print(f"    Events captured: {len(logger.events)}")

    # Verify: even numbers 1-100 = [2,4,...,100], squared = [4,16,...,10000]
    # filter > 1000: squares of 24,26,...,100 (even numbers whose square > 1000)
    expected_nums = [x**2 for x in range(2, 101, 2) if x**2 > 1000]
    assert result.output == sum(expected_nums)
    assert result.success
    print("\n  ✅ Demo 3 PASSED")


def demo_4_retry_and_failure_handling():
    """Demo 4: Pipeline with retries and graceful failure handling."""
    print("\n" + "=" * 70)
    print("DEMO 4: Retry Logic & Failure Handling")
    print("=" * 70)
    print(
        "Story: A flaky API stage that fails intermittently - retries save the day.\n"
    )

    call_count = {"value": 0}

    def flaky_enrichment(data):
        """Simulates an API that fails first 2 times, succeeds on 3rd."""
        call_count["value"] += 1
        if call_count["value"] <= 2:
            raise ConnectionError(f"API timeout (attempt {call_count['value']})")
        return [{"enriched": True, **row} for row in data]

    input_data = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]

    # Pipeline with retries
    retry_config = StageConfig(retries=3, retry_delay_ms=10)
    pipeline = (
        Pipeline("Retry Demo")
        .add_stage(FunctionStage("enrich_from_api", flaky_enrichment, retry_config))
        .add_stage(
            FunctionStage(
                "add_timestamp", lambda data: [{**r, "processed": True} for r in data]
            )
        )
    )
    pipeline.observe(LoggingObserver())

    result = pipeline.run(input_data)

    print(f"\n  Result: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"  API calls made: {call_count['value']} (2 failures + 1 success)")
    print(f"  Output records: {len(result.output)}")
    for rec in result.output:
        print(f"    {rec}")

    assert result.success
    assert call_count["value"] == 3
    assert all(r["enriched"] and r["processed"] for r in result.output)

    # Now test a pipeline that fails completely
    print("\n  --- Testing total failure (no retries) ---")

    def always_fails(data):
        """Perform the always fails step used by this project."""
        raise RuntimeError("Critical database error")

    fail_pipeline = Pipeline("Fail Demo").add_stage(
        FunctionStage(
            "bad_stage", always_fails, StageConfig(retries=1, retry_delay_ms=5)
        )
    )
    fail_result = fail_pipeline.run({"some": "data"})

    print(f"  Pipeline failed: {not fail_result.success}")
    print(f"  Failed stage: {fail_result.failed_stage}")
    assert not fail_result.success
    assert fail_result.failed_stage == "bad_stage"
    print("\n  ✅ Demo 4 PASSED")


def demo_5_builder_dsl_complex_pipeline():
    """Demo 5: Full Builder DSL for a complex ETL pipeline."""
    print("\n" + "=" * 70)
    print("DEMO 5: Builder DSL - Complex E-Commerce ETL")
    print("=" * 70)
    print("Story: Process e-commerce order data - clean, dedupe, enrich, aggregate.\n")

    csv_data = """order_id,customer,product,price,quantity,country
ORD001,alice@test.com,Laptop,999,1,US
ORD002,bob@test.com,Mouse,29,3,UK
ORD003,alice@test.com,Keyboard,79,2,US
ORD001,alice@test.com,Laptop,999,1,US
ORD004,charlie@test.com,Monitor,449,1,DE
ORD005,diana@test.com,Webcam,89,1,US
ORD006,eve@test.com,Chair,0,1,UK
ORD007,frank@test.com,Desk,299,2,DE
ORD008,grace@test.com,Headset,159,1,US"""

    builder = PipelineBuilder("E-Commerce ETL")
    pipeline = (
        builder.with_logging()
        .from_csv()
        .cast_types({"price": int, "quantity": int})
        .deduplicate("order_id")
        .validate(
            {
                "price": lambda p: p is not None and p > 0,
                "quantity": lambda q: q is not None and q > 0,
            }
        )
        .derive("total", lambda r: r["price"] * r["quantity"])
        .derive(
            "tier",
            lambda r: "premium" if r["price"] * r["quantity"] > 200 else "standard",
        )
        .normalize(["country"], lowercase=False)
        .build()
    )

    result = pipeline.run(csv_data)

    print(f"\n  Pipeline: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"  Stages executed: {len(result.stage_results)}")
    print(f"  Total duration: {result.total_duration_ms:.2f}ms")

    # Show results
    valid_orders = result.output
    print(f"\n  Input rows: 9 (including 1 duplicate, 1 invalid)")
    print(f"  Output records: {len(valid_orders)}")
    print(f"\n  Processed orders:")
    total_revenue = 0
    for order in valid_orders:
        total_revenue += order["total"]
        print(
            f"    {order['order_id']}: {order['product']:10s} ${order['total']:>6,} [{order['tier']}]"
        )

    print(f"\n  Total revenue: ${total_revenue:,}")
    print(f"  Premium orders: {sum(1 for o in valid_orders if o['tier'] == 'premium')}")
    print(
        f"  Standard orders: {sum(1 for o in valid_orders if o['tier'] == 'standard')}"
    )

    # Metrics from builder
    print(f"\n  Builder Metrics:")
    print(f"    Total pipeline time: {builder.metrics.total_duration:.2f}ms")

    # Assertions
    assert result.success
    assert len(valid_orders) == 7  # 9 - 1 duplicate - 1 invalid (price=0)
    assert all("total" in o and "tier" in o for o in valid_orders)
    print("\n  ✅ Demo 5 PASSED")


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║       P19 - DATA PIPELINE ETL FRAMEWORK                            ║")
    print("║       Pipeline Pattern | Builder | MapReduce | Observer             ║")
    print("╚══════════════════════════════════════════════════════════════════════╝\n")

    demo_1_basic_csv_pipeline()
    demo_2_mapreduce_aggregation()
    demo_3_pipeline_with_observers()
    demo_4_retry_and_failure_handling()
    demo_5_builder_dsl_complex_pipeline()

    print("\n" + "=" * 70)
    print("ALL 5 DEMOS PASSED ✅")
    print("=" * 70)
