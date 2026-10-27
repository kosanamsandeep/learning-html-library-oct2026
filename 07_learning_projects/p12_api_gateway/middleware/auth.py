"""
=============================================================================
PROJECT 12: API GATEWAY & RATE LIMITER
=============================================================================
FILE: middleware/auth.py
PURPOSE: Authentication middleware (API Key validation)

PROXY PATTERN: The gateway acts as a proxy — clients talk to the gateway,
gateway validates and forwards to backend services.
=============================================================================
"""

from middleware.base import Middleware, Request, Response


class AuthMiddleware(Middleware):
    """
    Authentication middleware: validates API keys before allowing access.

    CHAIN POSITION: Usually first or second in the chain.
    If auth fails → short-circuit with 401 (never reaches handler).
    """

    def __init__(self, valid_keys: dict[str, str] | None = None):
        """
        Args:
            valid_keys: dict of api_key → client_name
        """
        super().__init__()
        self._valid_keys = valid_keys or {
            "sk-prod-abc123": "client_a",
            "sk-prod-def456": "client_b",
            "sk-test-xyz789": "test_client",
        }
        # Paths that don't require auth
        self._public_paths = ["/health", "/status", "/docs"]

    def process(self, request: Request) -> Response:
        """Validate API key in request headers."""
        # Skip auth for public endpoints
        if request.path in self._public_paths:
            request.metadata["authenticated"] = False
            request.metadata["client_name"] = "anonymous"
            return self.handle(request)

        # Check for API key
        api_key = request.headers.get("X-API-Key", "")
        if not api_key:
            return Response(
                status_code=401,
                error="Missing API key. Include X-API-Key header.",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        # Validate key
        client_name = self._valid_keys.get(api_key)
        if client_name is None:
            return Response(
                status_code=403,
                error="Invalid API key",
            )

        # Auth passed — attach client info to request
        request.metadata["authenticated"] = True
        request.metadata["client_name"] = client_name
        request.metadata["api_key"] = api_key

        return self.handle(request)  # Pass to next middleware
