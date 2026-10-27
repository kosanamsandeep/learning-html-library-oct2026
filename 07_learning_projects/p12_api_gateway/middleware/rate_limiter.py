"""
=============================================================================
PROJECT 12: API GATEWAY & RATE LIMITER
=============================================================================
FILE: middleware/rate_limiter.py
PURPOSE: Token Bucket algorithm for rate limiting

TOKEN BUCKET ALGORITHM (Industry Standard):
- Bucket holds N tokens (capacity)
- Tokens refill at a fixed rate (e.g., 10/second)
- Each request costs 1 token
- If bucket empty → reject (429 Too Many Requests)

USED BY: Stripe, GitHub API, AWS API Gateway, Cloudflare

WHY TOKEN BUCKET over others:
- Allows bursts (unlike fixed window)
- Smooth rate over time (unlike sliding window)
- Simple to implement and reason about
=============================================================================
"""

import time
from middleware.base import Middleware, Request, Response


class TokenBucket:
    """
    TOKEN BUCKET: Classic rate limiting algorithm.

    ANALOGY: Imagine a bucket that holds tennis balls.
    - Bucket has a max capacity (e.g., 10 balls)
    - Balls are added at a fixed rate (e.g., 2/second)
    - Each API call removes 1 ball
    - If bucket is empty → request denied
    - Bucket never exceeds capacity (overflow discarded)

    MATH:
    - tokens += elapsed_time * refill_rate
    - tokens = min(tokens, capacity)
    - if tokens >= 1: allow, tokens -= 1
    - else: deny
    """

    def __init__(self, capacity: int = 10, refill_rate: float = 2.0):
        """
        Args:
            capacity: Max tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)  # Start full
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens. Returns True if allowed, False if rate-limited.
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self) -> None:
        """Add tokens based on elapsed time since last refill."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def get_remaining(self) -> int:
        """Return approximate remaining tokens."""
        self._refill()
        return int(self.tokens)


class RateLimiterMiddleware(Middleware):
    """
    Rate Limiting Middleware using per-client Token Buckets.

    Each unique client (by IP or API key) gets their own bucket.
    When bucket is empty → 429 Too Many Requests.

    HEADERS ADDED (following standard):
    - X-RateLimit-Limit: max requests
    - X-RateLimit-Remaining: requests left
    - Retry-After: seconds until next token (on 429)
    """

    def __init__(self, capacity: int = 10, refill_rate: float = 2.0):
        """Initialize the object with the dependencies or starting values it needs."""
        super().__init__()
        self._capacity = capacity
        self._refill_rate = refill_rate
        # Per-client buckets: key → TokenBucket
        self._buckets: dict[str, TokenBucket] = {}

    def _get_client_key(self, request: Request) -> str:
        """Identify the client (by API key or IP)."""
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            return f"key:{api_key}"
        return f"ip:{request.client_ip}"

    def _get_bucket(self, client_key: str) -> TokenBucket:
        """Get or create a token bucket for this client."""
        if client_key not in self._buckets:
            self._buckets[client_key] = TokenBucket(self._capacity, self._refill_rate)
        return self._buckets[client_key]

    def process(self, request: Request) -> Response:
        """Check rate limit before passing to next middleware."""
        client_key = self._get_client_key(request)
        bucket = self._get_bucket(client_key)

        if not bucket.consume():
            # Rate limited!
            retry_after = 1.0 / self._refill_rate
            return Response(
                status_code=429,
                error="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(self._capacity),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(int(retry_after)),
                },
            )

        # Allowed — add rate limit headers and continue
        request.metadata["rate_limit_remaining"] = bucket.get_remaining()

        response = self.handle(request)  # Pass to next middleware
        response.headers["X-RateLimit-Limit"] = str(self._capacity)
        response.headers["X-RateLimit-Remaining"] = str(bucket.get_remaining())
        return response
