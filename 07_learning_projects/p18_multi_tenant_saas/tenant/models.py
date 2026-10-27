"""
Tenant Management - Core multi-tenancy models and context.
Inspired by: Stripe's organization model, AWS Organizations, Shopify's tenant isolation

Multi-tenancy strategies:
  1. Shared DB, Shared Schema (rows tagged with tenant_id) - This project
  2. Shared DB, Separate Schema (one schema per tenant)
  3. Separate DB per tenant (full isolation)

We implement Strategy 1 (most common for SaaS) with proper isolation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from contextvars import ContextVar


class Plan(Enum):
    """Represents Plan in this learning project."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class PlanLimits:
    """Resource limits per plan."""

    max_users: int
    max_storage_mb: int
    max_api_calls_per_day: int
    features: set[str]


PLAN_LIMITS: dict[Plan, PlanLimits] = {
    Plan.FREE: PlanLimits(
        max_users=3,
        max_storage_mb=100,
        max_api_calls_per_day=1000,
        features={"basic_reports", "email_support"},
    ),
    Plan.STARTER: PlanLimits(
        max_users=10,
        max_storage_mb=1000,
        max_api_calls_per_day=10000,
        features={"basic_reports", "advanced_reports", "email_support", "api_access"},
    ),
    Plan.PROFESSIONAL: PlanLimits(
        max_users=50,
        max_storage_mb=10000,
        max_api_calls_per_day=100000,
        features={
            "basic_reports",
            "advanced_reports",
            "custom_reports",
            "email_support",
            "phone_support",
            "api_access",
            "webhooks",
            "sso",
        },
    ),
    Plan.ENTERPRISE: PlanLimits(
        max_users=9999,
        max_storage_mb=999999,
        max_api_calls_per_day=9999999,
        features={
            "basic_reports",
            "advanced_reports",
            "custom_reports",
            "email_support",
            "phone_support",
            "priority_support",
            "api_access",
            "webhooks",
            "sso",
            "audit_log",
            "custom_branding",
            "dedicated_infrastructure",
        },
    ),
}


@dataclass
class Tenant:
    """Represents a tenant (organization/company) in the SaaS platform."""

    tenant_id: str
    name: str
    plan: Plan
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = True
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def limits(self) -> PlanLimits:
        """Perform the limits step used by this project."""
        return PLAN_LIMITS[self.plan]


@dataclass
class TenantUser:
    """A user belonging to a specific tenant."""

    user_id: str
    tenant_id: str
    email: str
    role: str = "member"  # admin, member, viewer
    is_active: bool = True


# ─── Tenant Context (Thread-safe current tenant) ─────────────────

# ContextVar is the correct way to store per-request state in Python
# (works with asyncio, threading, etc.)
_current_tenant: ContextVar[Tenant | None] = ContextVar("current_tenant", default=None)


class TenantContext:
    """
    Manages the current tenant context.
    In a web app, this would be set by middleware from the request.
    Uses Python's ContextVar for thread-safety.
    """

    @staticmethod
    def set_current(tenant: Tenant) -> None:
        """Perform the set current step used by this project."""
        _current_tenant.set(tenant)

    @staticmethod
    def get_current() -> Tenant | None:
        """Return the requested item or information if it exists."""
        return _current_tenant.get()

    @staticmethod
    def require_current() -> Tenant:
        """Get current tenant or raise if not set."""
        tenant = _current_tenant.get()
        if tenant is None:
            raise TenantNotSetError("No tenant context set. Are you in a request?")
        return tenant

    @staticmethod
    def clear() -> None:
        """Perform the clear step used by this project."""
        _current_tenant.set(None)


class TenantNotSetError(Exception):
    """Domain-specific exception that makes this failure mode explicit and easy to catch in tests."""
    pass
