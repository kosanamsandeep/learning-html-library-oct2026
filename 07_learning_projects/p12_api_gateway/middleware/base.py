"""
=============================================================================
PROJECT 12: API GATEWAY & RATE LIMITER
=============================================================================
FILE: middleware/base.py
PURPOSE: Middleware Chain Pattern — Chain of Responsibility

PATTERNS: Chain of Responsibility, Decorator, Proxy, Token Bucket
REAL-WORLD: Express.js middleware, Django middleware, Kong/Nginx

MIDDLEWARE CHAIN:
Request → Auth → RateLimit → Logging → Transform → Handler → Response

Each middleware can:
1. Modify the request (add headers, parse tokens)
2. Short-circuit (reject unauthorized, rate-limited)
3. Pass to next middleware
4. Modify the response on the way back
=============================================================================
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Request:
    """Represents an incoming API request."""

    method: str = "GET"
    path: str = "/"
    headers: dict = field(default_factory=dict)
    body: Any = None
    query_params: dict = field(default_factory=dict)
    client_ip: str = "127.0.0.1"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)  # Middleware can attach data here


@dataclass
class Response:
    """Represents an API response."""

    status_code: int = 200
    body: Any = None
    headers: dict = field(default_factory=dict)
    error: str | None = None

    @property
    def is_success(self) -> bool:
        """Return True when the checked condition is satisfied."""
        return 200 <= self.status_code < 300


class Middleware(ABC):
    """
    CHAIN OF RESPONSIBILITY: Each middleware processes the request
    and optionally passes it to the next middleware in the chain.

    GOLDEN STANDARD:
    - Express.js: app.use(cors()); app.use(rateLimit()); ...
    - Django: MIDDLEWARE = ['SecurityMiddleware', 'SessionMiddleware', ...]
    - FastAPI: @app.middleware("http")
    """

    def __init__(self):
        """Initialize the object with the dependencies or starting values it needs."""
        self._next: Middleware | None = None

    def set_next(self, middleware: Middleware) -> Middleware:
        """Chain this middleware to the next one. Returns next for fluent API."""
        self._next = middleware
        return middleware

    def handle(self, request: Request) -> Response:
        """
        Process the request through this middleware.
        Default: pass to next if exists, else return 404.
        """
        if self._next:
            return self._next.process(request)
        return Response(status_code=404, error="No handler found")

    @abstractmethod
    def process(self, request: Request) -> Response:
        """Subclass implements specific middleware logic here."""
        pass
