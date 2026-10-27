"""
=============================================================================
PROJECT 12: API GATEWAY & RATE LIMITER
=============================================================================
FILE: middleware/logging_mw.py
PURPOSE: Request/Response logging middleware

DECORATOR PATTERN: Wraps the request/response with logging
without modifying the core logic.
=============================================================================
"""

from datetime import datetime
from middleware.base import Middleware, Request, Response


class LoggingMiddleware(Middleware):
    """
    Logs every request and response passing through the gateway.

    DECORATOR PATTERN: Adds behavior (logging) without modifying
    the request handler itself.
    """

    def __init__(self):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__()
        self.access_log: list[dict] = []

    def process(self, request: Request) -> Response:
        """Log request, pass to next, log response."""
        start = datetime.now()

        # Log incoming request
        log_entry = {
            "timestamp": start.isoformat(),
            "method": request.method,
            "path": request.path,
            "client_ip": request.client_ip,
            "client": request.metadata.get("client_name", "unknown"),
        }

        # Pass to next middleware/handler
        response = self.handle(request)

        # Log response
        log_entry["status_code"] = response.status_code
        log_entry["success"] = response.is_success
        self.access_log.append(log_entry)

        # Print structured log
        status_icon = "+" if response.is_success else "!"
        print(
            f"    [{status_icon}] {request.method} {request.path} -> {response.status_code} ({log_entry['client']})"
        )

        return response
