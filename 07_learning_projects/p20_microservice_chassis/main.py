"""
P20 - Microservice Chassis
============================
5 Demos showing the cross-cutting concerns every microservice needs.

Inspired by: Spring Boot, Go-Kit, Netflix OSS, Kubernetes patterns
Patterns: Service Registry, Health Checks, Structured Logging, Config, Lifecycle
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

import time
import os

from chassis.config import ConfigManager, ConfigSource
from chassis.logging import (
    StructuredLogger,
    LogLevel,
    set_correlation_id,
    get_correlation_id,
)
from chassis.health import HealthRegistry, HealthStatus, FunctionHealthIndicator
from chassis.registry import (
    ServiceRegistry,
    ServiceInstance,
    LoadBalanceStrategy,
    ServiceStatus,
)
from chassis.lifecycle import LifecycleManager, LifecycleComponent, LifecyclePhase


def demo_1_config_management():
    """Demo 1: Hierarchical configuration with priorities and validation."""
    print("=" * 70)
    print("DEMO 1: Configuration Management")
    print("=" * 70)
    print("Story: Service config from defaults → file → env → runtime overrides.\n")

    # Define config schema
    config = ConfigManager(prefix="MYAPP")
    config.define(
        "server.port",
        8080,
        "HTTP server port",
        validator=lambda v: 1024 <= int(v) <= 65535,
    )
    config.define("server.host", "0.0.0.0", "Bind address")
    config.define("db.url", "postgresql://localhost:5432/app", "Database URL")
    config.define("db.pool_size", 10, "Connection pool size")
    config.define("cache.ttl_seconds", 300, "Cache TTL")
    config.define("feature.dark_mode", False, "Dark mode feature flag")

    # Load "file" config (simulates reading from YAML/JSON)
    config.load_dict(
        {
            "db.url": "postgresql://prod-db:5432/myapp",
            "db.pool_size": 25,
            "cache.ttl_seconds": 600,
        }
    )

    # Set env var (simulates deployment environment)
    os.environ["MYAPP_SERVER_PORT"] = "9090"

    # Runtime override
    changes = []
    config.on_change(lambda k, old, new: changes.append((k, old, new)))
    config.override("feature.dark_mode", True)

    print("  Configuration Snapshot:")
    print("  " + "-" * 50)
    for key, info in config.snapshot().items():
        print(f"    {key:25s} = {str(info['value']):30s} [from: {info['source']}]")

    print(f"\n  Change events: {changes}")

    # Verify priority chain
    assert config.get("server.port") == "9090"  # From env
    assert config.get_source("server.port") == ConfigSource.ENVIRONMENT
    assert config.get("db.url") == "postgresql://prod-db:5432/myapp"  # From file
    assert config.get_source("db.url") == ConfigSource.FILE
    assert config.get("server.host") == "0.0.0.0"  # From default
    assert config.get_source("server.host") == ConfigSource.DEFAULT
    assert config.get("feature.dark_mode") is True  # From override
    assert config.get_source("feature.dark_mode") == ConfigSource.OVERRIDE

    # Cleanup
    del os.environ["MYAPP_SERVER_PORT"]
    print("\n  ✅ Demo 1 PASSED")


def demo_2_structured_logging():
    """Demo 2: JSON structured logging with correlation IDs."""
    print("\n" + "=" * 70)
    print("DEMO 2: Structured Logging with Correlation IDs")
    print("=" * 70)
    print("Story: Trace a request across service boundaries using correlation IDs.\n")

    # Create logger
    logger = StructuredLogger("order-service", level=LogLevel.INFO)

    # Simulate a request flow
    cid = set_correlation_id("req-abc123")
    print(f"  Correlation ID set: {cid}\n")

    logger.info("Request received", method="POST", path="/orders")
    logger.info("Validating order", items=3, total=299.99)

    # Child logger with bound context (like a sub-component)
    db_logger = logger.bind(component="database", pool="primary")
    db_logger.info("Query executed", query="INSERT INTO orders", duration_ms=12)
    db_logger.info("Transaction committed")

    # Simulate warning and error
    logger.warn("Inventory low", product="Widget-X", remaining=5)
    logger.info("Order confirmed", order_id="ORD-789")

    # This should NOT appear (below level)
    logger.debug("Debug detail that should be hidden")

    print(f"\n  Total log entries: {len(logger.entries)}")
    print(
        f"  All entries have correlation_id: {all(e.correlation_id == cid for e in logger.entries)}"
    )

    # JSON output mode
    print("\n  --- JSON Output Mode ---")
    json_logger = StructuredLogger(
        "payment-service", level=LogLevel.INFO, json_output=True
    )
    set_correlation_id("req-abc123")  # Same correlation ID (cross-service)
    json_logger.info("Payment processed", amount=299.99, currency="USD")
    json_logger.error("Refund failed", reason="insufficient_funds", order_id="ORD-789")

    assert len(logger.entries) == 6  # 6 logged (debug filtered out)
    assert all(e.correlation_id == "req-abc123" for e in logger.entries)
    print("\n  ✅ Demo 2 PASSED")


def demo_3_health_checks():
    """Demo 3: Liveness and readiness probes with health indicators."""
    print("\n" + "=" * 70)
    print("DEMO 3: Health Checks (Liveness & Readiness)")
    print("=" * 70)
    print("Story: Kubernetes probes checking if our service can serve traffic.\n")

    health = HealthRegistry("order-service")

    # Register health indicators
    health.register_liveness(
        FunctionHealthIndicator(
            "process_alive", lambda: {"healthy": True, "pid": 12345}
        )
    )

    health.register_readiness(
        FunctionHealthIndicator(
            "database", lambda: {"healthy": True, "pool_active": 5, "pool_max": 25}
        )
    )
    health.register_readiness(
        FunctionHealthIndicator(
            "redis_cache",
            lambda: {"healthy": True, "connected": True, "memory_mb": 128},
        )
    )
    health.register_readiness(
        FunctionHealthIndicator(
            "message_queue", lambda: {"healthy": True, "queue_depth": 42}
        )
    )

    # Run checks
    liveness = health.liveness()
    readiness = health.readiness()

    print("  Liveness Probe:")
    print(f"    Status: {liveness.status.value}")
    for check in liveness.checks:
        print(f"    - {check.name}: {check.status.value} ({check.duration_ms:.2f}ms)")

    print(f"\n  Readiness Probe:")
    print(f"    Status: {readiness.status.value}")
    for check in readiness.checks:
        print(f"    - {check.name}: {check.status.value} | {check.details}")

    # Simulate a failing component
    print("\n  --- Simulating database failure ---")
    health_with_failure = HealthRegistry("order-service")
    health_with_failure.register_readiness(
        FunctionHealthIndicator(
            "database",
            lambda: (_ for _ in ()).throw(ConnectionError("Connection refused")),
        )
    )
    health_with_failure.register_readiness(
        FunctionHealthIndicator("redis_cache", lambda: {"healthy": True})
    )

    degraded = health_with_failure.readiness()
    print(f"    Overall: {degraded.status.value}")
    for check in degraded.checks:
        print(f"    - {check.name}: {check.status.value} | {check.details}")

    assert liveness.status == HealthStatus.UP
    assert readiness.status == HealthStatus.UP
    assert degraded.status == HealthStatus.DOWN
    print("\n  ✅ Demo 3 PASSED")


def demo_4_service_registry():
    """Demo 4: Service registration, discovery, and load balancing."""
    print("\n" + "=" * 70)
    print("DEMO 4: Service Registry & Load Balancing")
    print("=" * 70)
    print("Story: Multiple instances register; clients discover and load-balance.\n")

    registry = ServiceRegistry(heartbeat_ttl_seconds=5.0)

    # Register multiple instances of services
    registry.register(
        "order-service",
        "order-1",
        "10.0.1.1",
        8080,
        {"version": "2.1.0", "region": "us-east"},
    )
    registry.register(
        "order-service",
        "order-2",
        "10.0.1.2",
        8080,
        {"version": "2.1.0", "region": "us-west"},
    )
    registry.register(
        "order-service",
        "order-3",
        "10.0.1.3",
        8080,
        {"version": "2.1.0", "region": "eu-west"},
    )
    registry.register(
        "payment-service", "pay-1", "10.0.2.1", 9090, {"version": "1.5.0"}
    )
    registry.register(
        "payment-service", "pay-2", "10.0.2.2", 9090, {"version": "1.5.0"}
    )

    print("  Registered Services:")
    for svc in registry.get_services():
        instances = registry.get_instances(svc)
        print(f"    {svc}: {len(instances)} instances")
        for inst in instances:
            print(f"      - {inst.instance_id} @ {inst.address} [{inst.metadata}]")

    # Load balancing: Round Robin
    print("\n  Round Robin resolution (order-service, 6 calls):")
    for i in range(6):
        inst = registry.resolve("order-service", LoadBalanceStrategy.ROUND_ROBIN)
        print(f"    Call {i+1}: → {inst.instance_id} @ {inst.address}")

    # Consistent Hash (same key always routes to same instance)
    print("\n  Consistent Hash (by customer_id):")
    for customer in ["cust-100", "cust-200", "cust-100", "cust-300", "cust-200"]:
        inst = registry.resolve(
            "order-service", LoadBalanceStrategy.CONSISTENT_HASH, key=customer
        )
        print(f"    {customer} → {inst.instance_id}")

    # Deregister and verify
    registry.deregister("order-service", "order-2")
    remaining = registry.get_instances("order-service")
    print(f"\n  After deregistering order-2: {len(remaining)} instances remain")

    assert len(remaining) == 2
    assert all(i.instance_id != "order-2" for i in remaining)
    print("\n  ✅ Demo 4 PASSED")


def demo_5_lifecycle_management():
    """Demo 5: Service lifecycle with startup/shutdown ordering."""
    print("\n" + "=" * 70)
    print("DEMO 5: Lifecycle Management (Startup & Shutdown)")
    print("=" * 70)
    print("Story: Service boots components in order, shuts down gracefully.\n")

    events = []

    class DatabaseComponent(LifecycleComponent):
        """Demo lifecycle component representing a database connection pool."""

        @property
        def name(self) -> str:
            """Return the component name used by the lifecycle manager."""
            return "database"

        def start(self):
            """Perform the start step used by this project."""
            events.append("DB started")
            print("    [database] Connected to PostgreSQL pool (25 connections)")

        def stop(self):
            """Perform the stop step used by this project."""
            events.append("DB stopped")
            print("    [database] Pool drained and connections closed")

    class CacheComponent(LifecycleComponent):
        """Demo lifecycle component representing a cache connection."""

        @property
        def name(self) -> str:
            """Return the component name used by the lifecycle manager."""
            return "cache"

        def start(self):
            """Perform the start step used by this project."""
            events.append("Cache started")
            print("    [cache] Redis connected (cluster mode)")

        def stop(self):
            """Perform the stop step used by this project."""
            events.append("Cache stopped")
            print("    [cache] Flushed pending writes, disconnected")

    class MessageQueueComponent(LifecycleComponent):
        """Demo lifecycle component representing a message queue connection."""

        @property
        def name(self) -> str:
            """Return the component name used by the lifecycle manager."""
            return "message_queue"

        def start(self):
            """Perform the start step used by this project."""
            events.append("MQ started")
            print("    [message_queue] Connected to RabbitMQ, consumers ready")

        def stop(self):
            """Perform the stop step used by this project."""
            events.append("MQ stopped")
            print("    [message_queue] Consumers stopped, channel closed")

    class HttpServerComponent(LifecycleComponent):
        """Demo lifecycle component representing the HTTP server."""

        @property
        def name(self) -> str:
            """Return the component name used by the lifecycle manager."""
            return "http_server"

        def start(self):
            """Perform the start step used by this project."""
            events.append("HTTP started")
            print("    [http_server] Listening on 0.0.0.0:8080")

        def stop(self):
            """Perform the stop step used by this project."""
            events.append("HTTP stopped")
            print("    [http_server] Graceful shutdown (waited for in-flight requests)")

    # Build lifecycle
    lifecycle = LifecycleManager("order-service")
    lifecycle.register(DatabaseComponent(), priority=10)
    lifecycle.register(CacheComponent(), priority=20)
    lifecycle.register(MessageQueueComponent(), priority=30)
    lifecycle.register(HttpServerComponent(), priority=100)  # Start last, stop first

    # Add hooks
    lifecycle.on(LifecyclePhase.STARTING, lambda: print("  ⏳ Starting service..."))
    lifecycle.on(LifecyclePhase.RUNNING, lambda: print("  🚀 Service is RUNNING"))
    lifecycle.on(LifecyclePhase.STOPPING, lambda: print("  ⏳ Stopping service..."))
    lifecycle.on(LifecyclePhase.STOPPED, lambda: print("  🛑 Service STOPPED"))

    # Start
    print("  --- STARTUP ---")
    success = lifecycle.start()
    print(f"\n  Phase: {lifecycle.phase.value}")
    print(f"  Status: {lifecycle.status()}")

    # Simulate running
    time.sleep(0.1)

    # Shutdown
    print("\n  --- SHUTDOWN ---")
    lifecycle.stop()
    print(f"\n  Phase: {lifecycle.phase.value}")

    # Verify ordering
    print(f"\n  Event Order: {events}")
    assert events == [
        "DB started",
        "Cache started",
        "MQ started",
        "HTTP started",
        "HTTP stopped",
        "MQ stopped",
        "Cache stopped",
        "DB stopped",
    ]
    assert lifecycle.phase == LifecyclePhase.STOPPED
    print("\n  ✅ Demo 5 PASSED")


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║       P20 - MICROSERVICE CHASSIS                                   ║")
    print("║       Config | Logging | Health | Registry | Lifecycle              ║")
    print("╚══════════════════════════════════════════════════════════════════════╝\n")

    demo_1_config_management()
    demo_2_structured_logging()
    demo_3_health_checks()
    demo_4_service_registry()
    demo_5_lifecycle_management()

    print("\n" + "=" * 70)
    print("ALL 5 DEMOS PASSED ✅")
    print("=" * 70)
