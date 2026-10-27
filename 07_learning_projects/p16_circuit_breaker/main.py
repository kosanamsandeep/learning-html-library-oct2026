"""
PROJECT 16: CIRCUIT BREAKER & RESILIENCE PATTERNS
==================================================
Patterns: Circuit Breaker, Retry with Backoff, Bulkhead, Fallback
Inspired by: Netflix Hystrix, resilience4j, Polly, Michael Nygard's "Release It!"

Story: You're running a microservice that depends on external services (payment
gateway, inventory, notifications). These services WILL fail. Without resilience
patterns, one slow/failing service can bring down your entire system.

Key Concepts Demonstrated:
  1. Circuit Breaker (prevent cascading failures)
  2. Retry with Exponential Backoff (handle transient failures)
  3. Bulkhead (isolate failure domains)
  4. Fallback (graceful degradation)
  5. Combined resilience stack
"""

import sys
import random

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Set seed for reproducible demos
random.seed(42)

from resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitOpenError,
)
from resilience.retry import RetryWithBackoff, RetryConfig
from resilience.bulkhead import Bulkhead, BulkheadConfig, BulkheadFullError
from services.external import PaymentService, InventoryService, NotificationService


def print_header():
    """Perform the print header step used by this project."""
    print("=" * 70)
    print("#  PROJECT 16: CIRCUIT BREAKER & RESILIENCE PATTERNS")
    print("#  Patterns: Circuit Breaker, Retry, Bulkhead, Fallback")
    print("#  Inspired by: Netflix Hystrix, resilience4j, Polly")
    print("=" * 70)


def demo_1_circuit_breaker():
    """Demo: Circuit breaker state transitions."""
    print("\n" + "=" * 70)
    print("  DEMO 1: Circuit Breaker (Preventing Cascading Failures)")
    print("=" * 70)

    # Create a payment service that fails 100% (simulating outage)
    payment = PaymentService(failure_rate=1.0)

    # Circuit breaker: opens after 3 failures, timeout 2 seconds
    cb = CircuitBreaker(
        CircuitBreakerConfig(
            name="payment-gateway",
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=2.0,
        )
    )

    # Track state changes
    state_changes = []
    cb.on_state_change(
        lambda old, new: state_changes.append(f"{old.value} -> {new.value}")
    )

    print(f"\n  Circuit Breaker: '{cb.name}'")
    print(f"  Config: failure_threshold=3, timeout=2s")
    print(f"  Payment service: 100% failure rate (simulating outage)\n")

    # Send requests
    for i in range(8):
        try:
            result = cb.call(payment.process_payment, 99.99)
            print(f"    Request {i+1}: SUCCESS | State: {cb.state.value}")
        except CircuitOpenError as e:
            print(
                f"    Request {i+1}: REJECTED (circuit open) | State: {cb.state.value}"
            )
        except ConnectionError as e:
            print(f"    Request {i+1}: FAILED  | State: {cb.state.value}")

    print(f"\n  State changes: {state_changes}")
    print(f"\n  Stats:")
    print(f"    Total calls: {cb.stats.total_calls}")
    print(f"    Successful: {cb.stats.successful_calls}")
    print(f"    Failed: {cb.stats.failed_calls}")
    print(f"    Rejected (fast-fail): {cb.stats.rejected_calls}")

    print(f"\n  Key insight: After 3 failures, circuit OPENS.")
    print(f"  Subsequent requests fail FAST without calling the service.")
    print(f"  This prevents overloading a struggling service.")


def demo_2_recovery():
    """Demo: Circuit breaker recovery (OPEN -> HALF_OPEN -> CLOSED)."""
    print("\n" + "=" * 70)
    print("  DEMO 2: Circuit Recovery (Half-Open State)")
    print("=" * 70)

    # Service that fails then recovers
    call_count = [0]

    def unstable_service():
        """Perform the unstable service step used by this project."""
        call_count[0] += 1
        if call_count[0] <= 3:  # First 3 calls fail
            raise ConnectionError("Service down")
        return {"status": "ok", "call": call_count[0]}

    cb = CircuitBreaker(
        CircuitBreakerConfig(
            name="recovery-demo",
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=0.1,  # Very short for demo
        )
    )

    state_log = []
    cb.on_state_change(lambda old, new: state_log.append((old.value, new.value)))

    print(f"\n  Phase 1: Service is DOWN (3 failures trip the breaker)")
    for i in range(4):
        try:
            cb.call(unstable_service)
            print(f"    Call {i+1}: SUCCESS | State: {cb.state.value}")
        except CircuitOpenError:
            print(f"    Call {i+1}: REJECTED | State: {cb.state.value}")
        except ConnectionError:
            print(f"    Call {i+1}: FAILED  | State: {cb.state.value}")

    print(
        f"\n  Phase 2: Waiting for timeout (simulating {cb._config.timeout_seconds}s)..."
    )
    import time

    time.sleep(0.15)  # Wait for timeout

    print(f"  State after timeout: {cb.state.value}")
    print(f"\n  Phase 3: Service RECOVERED - testing in HALF_OPEN")
    for i in range(3):
        try:
            result = cb.call(unstable_service)
            print(f"    Call {i+5}: SUCCESS | State: {cb.state.value}")
        except CircuitOpenError:
            print(f"    Call {i+5}: REJECTED | State: {cb.state.value}")
        except ConnectionError:
            print(f"    Call {i+5}: FAILED  | State: {cb.state.value}")

    print(f"\n  State transitions: {state_log}")
    print(f"  Final state: {cb.state.value}")
    print(f"\n  Key insight: After timeout, breaker enters HALF_OPEN.")
    print(f"  If test requests succeed, it CLOSES (normal operation resumes).")


def demo_3_retry_backoff():
    """Demo: Retry with exponential backoff."""
    print("\n" + "=" * 70)
    print("  DEMO 3: Retry with Exponential Backoff")
    print("=" * 70)

    # Service that fails first 2 times, succeeds on 3rd
    attempt = [0]

    def flaky_service():
        """Perform the flaky service step used by this project."""
        attempt[0] += 1
        if attempt[0] <= 2:
            raise ConnectionError(f"Temporary failure (attempt {attempt[0]})")
        return {"status": "success", "attempt": attempt[0]}

    retry = RetryWithBackoff(
        RetryConfig(
            max_retries=4,
            base_delay=1.0,
            exponential_base=2.0,
            jitter=False,  # Disable jitter for predictable demo
        )
    )

    print(f"\n  Config: max_retries=4, base_delay=1s, exponential_base=2x")
    print(f"  Service: fails first 2 times, succeeds on 3rd\n")

    result = retry.execute(flaky_service)
    print(f"    Success: {result.success}")
    print(f"    Attempts: {result.attempts}")
    print(f"    Delays between retries: {result.delays}")
    print(f"    Total wait time: {result.total_delay:.1f}s")
    print(f"    Result: {result.result}")

    # Show backoff calculation
    print(f"\n  Backoff calculation (without jitter):")
    retry_no_jitter = RetryWithBackoff(
        RetryConfig(max_retries=6, base_delay=1.0, exponential_base=2.0, jitter=False)
    )
    print(f"    Attempt 0: delay = 1.0 * 2^0 = 1.0s")
    print(f"    Attempt 1: delay = 1.0 * 2^1 = 2.0s")
    print(f"    Attempt 2: delay = 1.0 * 2^2 = 4.0s")
    print(f"    Attempt 3: delay = 1.0 * 2^3 = 8.0s")
    print(f"    Attempt 4: delay = 1.0 * 2^4 = 16.0s")
    print(f"    Attempt 5: delay = min(1.0 * 2^5, 30.0) = 30.0s (capped)")

    print(f"\n  With jitter (real-world):")
    print(f"    delay = random(0, calculated_delay)")
    print(f"    Prevents 'thundering herd' - all retries hitting at same time")


def demo_4_bulkhead():
    """Demo: Bulkhead pattern isolating failure domains."""
    print("\n" + "=" * 70)
    print("  DEMO 4: Bulkhead Pattern (Failure Isolation)")
    print("=" * 70)

    # Create bulkheads for different services
    payment_bulkhead = Bulkhead(BulkheadConfig(name="payment", max_concurrent=3))
    inventory_bulkhead = Bulkhead(BulkheadConfig(name="inventory", max_concurrent=5))

    print(f"\n  Bulkheads configured:")
    print(f"    Payment:   max {payment_bulkhead._config.max_concurrent} concurrent")
    print(f"    Inventory: max {inventory_bulkhead._config.max_concurrent} concurrent")

    # Simulate payment service becoming slow (holds connections)
    print(f"\n  Scenario: Payment service becomes slow (holds 3 connections)")

    # Manually simulate concurrent usage
    payment_bulkhead._active = 3  # Simulating 3 in-flight requests

    print(
        f"    Payment bulkhead: {payment_bulkhead._active}/{payment_bulkhead._config.max_concurrent} active"
    )
    print(
        f"    Inventory bulkhead: {inventory_bulkhead._active}/{inventory_bulkhead._config.max_concurrent} active"
    )

    # Try to use payment (should be rejected)
    try:
        payment_bulkhead.call(lambda: {"payment": "ok"})
        print(f"\n    New payment request: ALLOWED")
    except BulkheadFullError as e:
        print(f"\n    New payment request: REJECTED (bulkhead full)")

    # Inventory still works fine!
    try:
        result = inventory_bulkhead.call(lambda: {"stock": 42})
        print(f"    New inventory request: ALLOWED (isolated from payment!)")
    except BulkheadFullError:
        print(f"    New inventory request: REJECTED")

    print(f"\n  Key insight: Payment being slow doesn't affect inventory!")
    print(f"  Each service has its own resource pool (bulkhead).")
    print(f"  Like ship compartments - one floods, others stay dry.")


def demo_5_combined_resilience():
    """Demo: Combining all patterns into a resilience stack."""
    print("\n" + "=" * 70)
    print("  DEMO 5: Combined Resilience Stack")
    print("=" * 70)

    # A service with 40% failure rate
    payment = PaymentService(failure_rate=0.4)

    # Stack: Bulkhead -> Circuit Breaker -> Retry -> Service Call
    bulkhead = Bulkhead(BulkheadConfig(name="payment", max_concurrent=5))
    circuit = CircuitBreaker(
        CircuitBreakerConfig(
            name="payment-cb",
            failure_threshold=4,
            success_threshold=2,
            timeout_seconds=1.0,
        )
    )
    retry = RetryWithBackoff(RetryConfig(max_retries=2, base_delay=0.5, jitter=False))

    def resilient_payment(amount: float) -> dict:
        """Payment call wrapped in full resilience stack."""

        # Layer 1: Bulkhead (limit concurrent)
        def with_circuit():
            # Layer 2: Circuit Breaker (fail fast if service is down)
            """Perform the with circuit step used by this project."""
            def with_retry():
                # Layer 3: Retry (handle transient failures)
                """Perform the with retry step used by this project."""
                result = retry.execute(payment.process_payment, amount)
                if not result.success:
                    raise result.last_exception
                return result.result

            return circuit.call(with_retry)

        return bulkhead.call(with_circuit)

    print(f"\n  Resilience Stack (outermost first):")
    print(f"    1. Bulkhead (max 5 concurrent)")
    print(f"    2. Circuit Breaker (trips after 4 failures)")
    print(f"    3. Retry (2 retries with 0.5s backoff)")
    print(f"    4. Payment Service (40% failure rate)")

    print(f"\n  Processing 12 payments:")
    successes = 0
    failures = 0
    rejected = 0

    for i in range(12):
        try:
            result = resilient_payment(49.99)
            successes += 1
            status = "OK"
        except CircuitOpenError:
            rejected += 1
            status = "CIRCUIT_OPEN"
        except BulkheadFullError:
            rejected += 1
            status = "BULKHEAD_FULL"
        except Exception as e:
            failures += 1
            status = f"FAILED ({type(e).__name__})"

        print(f"    Payment {i+1:2d}: {status:20s} | CB: {circuit.state.value:9s}")

    print(f"\n  Results:")
    print(f"    Successes: {successes}")
    print(f"    Failures: {failures}")
    print(f"    Rejected (fast-fail): {rejected}")
    print(
        f"    Payment service calls: {payment.call_count} (without resilience: would be 12)"
    )

    print(f"\n  Key insight: The resilience stack REDUCES load on failing service")
    print(f"  while maximizing success rate for the caller.")


def print_summary():
    """Perform the print summary step used by this project."""
    print("\n" + "=" * 70)
    print("  LEARNING SUMMARY")
    print("=" * 70)
    print("""
  CIRCUIT BREAKER:
     - CLOSED: Normal flow, count failures
     - OPEN: Fail fast, don't call service (protect it)
     - HALF_OPEN: Test with single request
     - Prevents cascading failures across services

  RETRY WITH BACKOFF:
     - Handles transient failures (network blips)
     - Exponential backoff: wait longer each retry
     - Jitter: randomize to prevent thundering herd
     - Cap maximum delay

  BULKHEAD:
     - Isolate resource usage per service
     - One slow service can't exhaust all connections
     - Like ship compartments (name origin)
     - Implemented as semaphore/thread pool

  RESILIENCE STACK (Order matters!):
     Bulkhead -> Circuit Breaker -> Retry -> Service Call
     - Bulkhead: limit concurrency (outermost)
     - Circuit Breaker: fast-fail if service is down
     - Retry: handle transient failures (innermost)

  REAL-WORLD IMPLEMENTATIONS:
     - Netflix Hystrix (Java, now in maintenance)
     - resilience4j (Java, Hystrix successor)
     - Polly (.NET resilience library)
     - Tenacity (Python retry library)
     - AWS SDK: built-in retry with backoff
    """)


if __name__ == "__main__":
    print_header()
    demo_1_circuit_breaker()
    demo_2_recovery()
    demo_3_retry_backoff()
    demo_4_bulkhead()
    demo_5_combined_resilience()
    print_summary()
