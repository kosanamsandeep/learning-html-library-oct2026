"""
Simulated external services that can fail in various ways.
These represent real microservices that might be unreliable.
"""

from __future__ import annotations
import random


class PaymentService:
    """Simulates an external payment gateway (Stripe, PayPal)."""

    def __init__(self, failure_rate: float = 0.0, latency_ms: int = 0):
        """Initialize the object with the dependencies or starting values it needs."""
        self._failure_rate = failure_rate
        self._latency_ms = latency_ms
        self._call_count = 0

    def process_payment(self, amount: float, card: str = "****1234") -> dict:
        """Run the main processing logic for the provided input."""
        self._call_count += 1
        if random.random() < self._failure_rate:
            raise ConnectionError(
                f"Payment gateway timeout (attempt #{self._call_count})"
            )
        return {
            "status": "success",
            "amount": amount,
            "card": card,
            "tx_id": f"TX-{self._call_count:04d}",
        }

    @property
    def call_count(self) -> int:
        """Perform the call count step used by this project."""
        return self._call_count


class InventoryService:
    """Simulates an inventory microservice."""

    def __init__(self, failure_rate: float = 0.0):
        """Initialize the object with the dependencies or starting values it needs."""
        self._failure_rate = failure_rate
        self._call_count = 0
        self._stock = {"SKU-001": 100, "SKU-002": 50, "SKU-003": 5}

    def check_stock(self, sku: str) -> dict:
        """Perform the check stock step used by this project."""
        self._call_count += 1
        if random.random() < self._failure_rate:
            raise TimeoutError(
                f"Inventory service unavailable (attempt #{self._call_count})"
            )
        stock = self._stock.get(sku, 0)
        return {
            "sku": sku,
            "available": stock,
            "status": "in_stock" if stock > 0 else "out_of_stock",
        }

    @property
    def call_count(self) -> int:
        """Perform the call count step used by this project."""
        return self._call_count


class NotificationService:
    """Simulates an email/SMS notification service."""

    def __init__(self, failure_rate: float = 0.0):
        """Initialize the object with the dependencies or starting values it needs."""
        self._failure_rate = failure_rate
        self._call_count = 0
        self._sent: list[str] = []

    def send_email(self, to: str, subject: str) -> dict:
        """Perform the send email step used by this project."""
        self._call_count += 1
        if random.random() < self._failure_rate:
            raise IOError(f"SMTP connection refused (attempt #{self._call_count})")
        self._sent.append(f"{to}: {subject}")
        return {"status": "sent", "to": to, "subject": subject}

    @property
    def call_count(self) -> int:
        """Perform the call count step used by this project."""
        return self._call_count


class DatabaseService:
    """Simulates a database that can become overloaded."""

    def __init__(self, max_connections: int = 5):
        """Initialize the object with the dependencies or starting values it needs."""
        self._max_connections = max_connections
        self._active_connections = 0
        self._call_count = 0

    def query(self, sql: str) -> dict:
        """Perform the query step used by this project."""
        self._call_count += 1
        if self._active_connections >= self._max_connections:
            raise ConnectionError(
                f"Connection pool exhausted ({self._active_connections}/{self._max_connections})"
            )
        self._active_connections += 1
        try:
            return {"rows": [{"id": 1, "data": "result"}], "query": sql}
        finally:
            self._active_connections -= 1

    @property
    def call_count(self) -> int:
        """Perform the call count step used by this project."""
        return self._call_count
