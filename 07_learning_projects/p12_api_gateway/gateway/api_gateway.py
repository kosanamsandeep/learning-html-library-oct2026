"""
=============================================================================
PROJECT 12: API GATEWAY & RATE LIMITER
=============================================================================
FILE: gateway/api_gateway.py
PURPOSE: The Gateway that wires middleware chain + routes requests

API GATEWAY PATTERN:
- Single entry point for all API traffic
- Routes requests to backend services
- Applies cross-cutting concerns (auth, rate limit, logging)
- Like Kong, AWS API Gateway, Nginx reverse proxy

BUILDS THE CHAIN:
  Auth → RateLimit → Logging → Router → Handler
=============================================================================
"""

from middleware.base import Middleware, Request, Response
from middleware.auth import AuthMiddleware
from middleware.rate_limiter import RateLimiterMiddleware
from middleware.logging_mw import LoggingMiddleware
from typing import Callable

# Route handler type
RouteHandler = Callable[[Request], Response]


class Router(Middleware):
    """Routes requests to registered handlers based on method + path."""

    def __init__(self):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__()
        self._routes: dict[str, RouteHandler] = {}

    def register(self, method: str, path: str, handler: RouteHandler) -> None:
        """Perform the register step used by this project."""
        key = f"{method.upper()}:{path}"
        self._routes[key] = handler

    def process(self, request: Request) -> Response:
        """Perform the process step used by this project."""
        key = f"{request.method.upper()}:{request.path}"
        handler = self._routes.get(key)
        if handler:
            return handler(request)
        return Response(
            status_code=404, error=f"Route not found: {request.method} {request.path}"
        )


class APIGateway:
    """
    API GATEWAY: Single entry point that wires middleware + routes.

    CONSTRUCTION:
    1. Create middleware instances
    2. Chain them: auth → rate_limit → logging → router
    3. Register route handlers on the router
    4. All requests enter through gateway.handle(request)

    REAL-WORLD EQUIVALENT:
    - Kong: plugins (auth, rate-limit, logging) + routes
    - AWS API Gateway: authorizers + throttling + integrations
    - Express.js: app.use(middleware) + app.get(path, handler)
    """

    def __init__(self, rate_limit: int = 10, refill_rate: float = 5.0):
        # Create middleware instances
        """Initialize the object with the dependencies or starting values it needs."""
        self._auth = AuthMiddleware()
        self._rate_limiter = RateLimiterMiddleware(
            capacity=rate_limit, refill_rate=refill_rate
        )
        self._logger = LoggingMiddleware()
        self._router = Router()

        # Build the chain: Auth → RateLimit → Logging → Router
        self._auth.set_next(self._rate_limiter)
        self._rate_limiter.set_next(self._logger)
        self._logger.set_next(self._router)

        # Entry point is the first middleware
        self._entry = self._auth

    def register_route(self, method: str, path: str, handler: RouteHandler) -> None:
        """Register a route handler."""
        self._router.register(method, path, handler)

    def handle(self, request: Request) -> Response:
        """Process a request through the full middleware chain."""
        return self._entry.process(request)

    def get_access_log(self) -> list[dict]:
        """Return the access log from the logging middleware."""
        return self._logger.access_log

    def get_stats(self) -> dict:
        """Return gateway statistics."""
        log = self._logger.access_log
        return {
            "total_requests": len(log),
            "successful": sum(1 for e in log if e["success"]),
            "failed": sum(1 for e in log if not e["success"]),
        }
