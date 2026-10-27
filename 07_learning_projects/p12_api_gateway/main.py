"""
=============================================================================
PROJECT 12: API GATEWAY & RATE LIMITER — MAIN DEMO
=============================================================================
RUN: cd p12_api_gateway && python main.py
=============================================================================
"""

import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from middleware.base import Request, Response
from gateway.api_gateway import APIGateway


def print_header(title: str):
    """Perform the print header step used by this project."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


# --- Simulated Backend Handlers ---
def get_users(req: Request) -> Response:
    """Return the requested item or information if it exists."""
    return Response(status_code=200, body={"users": ["Alice", "Bob", "Charlie"]})


def get_user(req: Request) -> Response:
    """Return the requested item or information if it exists."""
    return Response(
        status_code=200, body={"user": "Alice", "email": "alice@example.com"}
    )


def create_order(req: Request) -> Response:
    """Create a new domain object or record from the provided input."""
    return Response(status_code=201, body={"order_id": "ORD-123", "status": "created"})


def health_check(req: Request) -> Response:
    """Perform the health check step used by this project."""
    return Response(status_code=200, body={"status": "healthy"})


def demo_middleware_chain():
    """DEMO 1: Full middleware chain processing."""
    print_header("DEMO 1: Middleware Chain (Auth -> RateLimit -> Log -> Route)")

    gateway = APIGateway(rate_limit=5, refill_rate=2.0)
    gateway.register_route("GET", "/users", get_users)
    gateway.register_route("GET", "/user/1", get_user)
    gateway.register_route("POST", "/orders", create_order)
    gateway.register_route("GET", "/health", health_check)

    # Successful authenticated request
    print("\n  1. Valid API key request:")
    resp = gateway.handle(
        Request(
            method="GET",
            path="/users",
            headers={"X-API-Key": "sk-prod-abc123"},
            client_ip="10.0.0.1",
        )
    )
    print(f"     Response: {resp.status_code} | Body: {resp.body}")

    # Public endpoint (no auth needed)
    print("\n  2. Public endpoint (no auth):")
    resp = gateway.handle(Request(method="GET", path="/health", client_ip="10.0.0.2"))
    print(f"     Response: {resp.status_code} | Body: {resp.body}")

    # Missing API key
    print("\n  3. Missing API key:")
    resp = gateway.handle(Request(method="GET", path="/users", client_ip="10.0.0.3"))
    print(f"     Response: {resp.status_code} | Error: {resp.error}")

    # Invalid API key
    print("\n  4. Invalid API key:")
    resp = gateway.handle(
        Request(
            method="GET",
            path="/users",
            headers={"X-API-Key": "sk-invalid"},
            client_ip="10.0.0.4",
        )
    )
    print(f"     Response: {resp.status_code} | Error: {resp.error}")

    # Route not found
    print("\n  5. Unknown route:")
    resp = gateway.handle(
        Request(
            method="DELETE",
            path="/users/99",
            headers={"X-API-Key": "sk-prod-abc123"},
            client_ip="10.0.0.1",
        )
    )
    print(f"     Response: {resp.status_code} | Error: {resp.error}")


def demo_rate_limiting():
    """DEMO 2: Rate limiting with Token Bucket."""
    print_header("DEMO 2: Rate Limiting (Token Bucket Algorithm)")

    # Very low limit for demo
    gateway = APIGateway(rate_limit=3, refill_rate=1.0)
    gateway.register_route("GET", "/data", lambda r: Response(200, body={"data": "ok"}))

    print("\n  Bucket capacity=3, refill_rate=1/sec")
    print("  Sending 6 rapid requests from same client:\n")

    for i in range(6):
        resp = gateway.handle(
            Request(
                method="GET",
                path="/data",
                headers={"X-API-Key": "sk-prod-abc123"},
                client_ip="192.168.1.100",
            )
        )
        status = "ALLOWED" if resp.is_success else "RATE LIMITED (429)"
        remaining = resp.headers.get("X-RateLimit-Remaining", "?")
        print(f"    Request {i+1}: {status} | Remaining: {remaining}")

    print("\n  Key insight: First 3 allowed (bucket had 3 tokens),")
    print("  subsequent rejected until tokens refill.")


def demo_per_client_isolation():
    """DEMO 3: Each client gets their own rate limit bucket."""
    print_header("DEMO 3: Per-Client Rate Limit Isolation")

    gateway = APIGateway(rate_limit=2, refill_rate=1.0)
    gateway.register_route("GET", "/api", lambda r: Response(200, body={"ok": True}))

    print("\n  Two different clients, each with capacity=2:")
    print("  Client A and Client B make requests:\n")

    clients = [
        ("sk-prod-abc123", "Client A"),
        ("sk-prod-abc123", "Client A"),
        ("sk-prod-abc123", "Client A"),  # Should be rate-limited
        ("sk-prod-def456", "Client B"),  # Fresh bucket!
        ("sk-prod-def456", "Client B"),
        ("sk-prod-def456", "Client B"),  # Should be rate-limited
    ]

    for key, name in clients:
        resp = gateway.handle(
            Request(
                method="GET",
                path="/api",
                headers={"X-API-Key": key},
            )
        )
        status = "OK" if resp.is_success else "429"
        print(f"    {name}: {status}")

    print("\n  Key insight: Each API key gets an independent bucket.")
    print("  Client B isn't affected by Client A's usage.")


def demo_gateway_stats():
    """DEMO 4: Gateway observability."""
    print_header("DEMO 4: Gateway Observability & Access Logs")

    gateway = APIGateway(rate_limit=10, refill_rate=5.0)
    gateway.register_route("GET", "/users", get_users)
    gateway.register_route("POST", "/orders", create_order)

    # Generate some traffic
    requests_to_send = [
        Request(method="GET", path="/users", headers={"X-API-Key": "sk-prod-abc123"}),
        Request(method="POST", path="/orders", headers={"X-API-Key": "sk-prod-def456"}),
        Request(method="GET", path="/users", headers={"X-API-Key": "sk-prod-abc123"}),
        Request(method="GET", path="/unknown", headers={"X-API-Key": "sk-prod-abc123"}),
        Request(method="GET", path="/users"),  # No API key
    ]

    print("\n  Sending mixed traffic:\n")
    for req in requests_to_send:
        gateway.handle(req)

    print(f"\n  Gateway Stats: {gateway.get_stats()}")
    print(f"\n  Access Log:")
    for entry in gateway.get_access_log():
        print(
            f"    {entry['method']} {entry['path']} -> {entry['status_code']} ({entry['client']})"
        )


def main():
    """Perform the main step used by this project."""
    print("\n" + "#" * 70)
    print("#  PROJECT 12: API GATEWAY & RATE LIMITER                            #")
    print("#  Patterns: Chain of Responsibility, Token Bucket, Proxy, Decorator #")
    print("#  Inspired by: Kong, AWS API Gateway, Express.js, Stripe API        #")
    print("#" * 70)

    demo_middleware_chain()
    demo_rate_limiting()
    demo_per_client_isolation()
    demo_gateway_stats()

    print_header("LEARNING SUMMARY")
    print("""
  CHAIN OF RESPONSIBILITY (Middleware):
     Request flows through a chain: Auth -> Rate Limit -> Log -> Route
     Each can short-circuit (reject) or pass to next

  TOKEN BUCKET (Rate Limiting):
     - Bucket holds N tokens, refills at fixed rate
     - Each request costs 1 token
     - Empty bucket = 429 Too Many Requests
     - Per-client isolation

  PROXY PATTERN (Gateway):
     - Single entry point for all API traffic
     - Clients don't talk to backends directly
     - Cross-cutting concerns applied uniformly

  DECORATOR PATTERN (Logging):
     - Adds behavior (logging) without modifying handler logic
     - Wraps request/response transparently
    """)


if __name__ == "__main__":
    main()
