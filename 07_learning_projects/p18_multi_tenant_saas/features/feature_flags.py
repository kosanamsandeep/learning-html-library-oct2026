"""
Feature Flag System - Control feature rollout per tenant/plan.
Inspired by: LaunchDarkly, Unleash, Flagsmith, Split.io

Feature flags allow:
  - Gradual rollout (10% of tenants first)
  - Plan-based gating (enterprise only)
  - A/B testing
  - Kill switch for broken features
  - Tenant-specific overrides
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import hashlib

from tenant.models import Tenant, Plan


class FlagStrategy(Enum):
    """Implements one interchangeable algorithm behind a common interface."""
    BOOLEAN = "boolean"  # Simple on/off
    PLAN_BASED = "plan_based"  # Available for certain plans
    PERCENTAGE = "percentage"  # Gradual rollout by percentage
    TENANT_LIST = "tenant_list"  # Specific tenant whitelist


@dataclass
class FeatureFlag:
    """Definition of a feature flag."""

    key: str
    name: str
    description: str = ""
    strategy: FlagStrategy = FlagStrategy.BOOLEAN
    enabled: bool = True
    # Strategy-specific config
    allowed_plans: set[Plan] = field(default_factory=set)
    rollout_percentage: int = 100
    allowed_tenants: set[str] = field(default_factory=set)
    # Override per tenant
    tenant_overrides: dict[str, bool] = field(default_factory=dict)


class FeatureFlagService:
    """
    Evaluates feature flags for a given tenant.
    Supports multiple evaluation strategies.
    """

    def __init__(self):
        """Initialize the object with the dependencies or starting values it needs."""
        self._flags: dict[str, FeatureFlag] = {}

    def register_flag(self, flag: FeatureFlag) -> None:
        """Perform the register flag step used by this project."""
        self._flags[flag.key] = flag

    def is_enabled(self, key: str, tenant: Tenant) -> bool:
        """Check if a feature is enabled for the given tenant."""
        if key not in self._flags:
            return False

        flag = self._flags[key]

        # Master kill switch
        if not flag.enabled:
            return False

        # Tenant-specific override (highest priority)
        if tenant.tenant_id in flag.tenant_overrides:
            return flag.tenant_overrides[tenant.tenant_id]

        # Evaluate based on strategy
        if flag.strategy == FlagStrategy.BOOLEAN:
            return flag.enabled

        elif flag.strategy == FlagStrategy.PLAN_BASED:
            return tenant.plan in flag.allowed_plans

        elif flag.strategy == FlagStrategy.PERCENTAGE:
            return self._is_in_rollout(tenant.tenant_id, flag.rollout_percentage)

        elif flag.strategy == FlagStrategy.TENANT_LIST:
            return tenant.tenant_id in flag.allowed_tenants

        return False

    def _is_in_rollout(self, tenant_id: str, percentage: int) -> bool:
        """
        Deterministic percentage rollout based on tenant_id hash.
        Same tenant always gets same result (consistent assignment).
        """
        hash_val = int(hashlib.md5(tenant_id.encode()).hexdigest()[:8], 16)
        bucket = hash_val % 100
        return bucket < percentage

    def get_all_flags(self, tenant: Tenant) -> dict[str, bool]:
        """Get all flag values for a tenant."""
        return {key: self.is_enabled(key, tenant) for key in self._flags}

    def list_flags(self) -> list[FeatureFlag]:
        """Return a collection of items for display or further processing."""
        return list(self._flags.values())
