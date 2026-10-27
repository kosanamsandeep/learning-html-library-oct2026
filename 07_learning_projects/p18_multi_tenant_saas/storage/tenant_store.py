"""
Tenant-Isolated Storage - Data access with automatic tenant scoping.
Inspired by: Django's multi-tenant packages, Citus (distributed Postgres), Row-Level Security

Every query is automatically scoped to the current tenant.
Tenants can NEVER see each other's data.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from tenant.models import Tenant, TenantContext


@dataclass
class Record:
    """A data record with tenant ownership."""

    record_id: str
    tenant_id: str
    collection: str
    data: dict = field(default_factory=dict)


class TenantScopedStore:
    """
    In-memory data store with automatic tenant isolation.

    Every operation is scoped to the current tenant context.
    This simulates what Postgres Row-Level Security (RLS) does,
    or what Django's tenant middleware provides.
    """

    def __init__(self):
        # Storage: {collection: {record_id: Record}}
        """Initialize the object with the dependencies or starting values it needs."""
        self._data: dict[str, dict[str, Record]] = {}
        self._usage: dict[str, int] = {}  # tenant_id -> record count

    def insert(self, collection: str, record_id: str, data: dict) -> Record:
        """Insert a record (automatically tagged with current tenant)."""
        tenant = TenantContext.require_current()

        record = Record(
            record_id=record_id,
            tenant_id=tenant.tenant_id,
            collection=collection,
            data=data,
        )

        if collection not in self._data:
            self._data[collection] = {}
        self._data[collection][f"{tenant.tenant_id}:{record_id}"] = record
        self._usage[tenant.tenant_id] = self._usage.get(tenant.tenant_id, 0) + 1
        return record

    def find(self, collection: str, record_id: str) -> Record | None:
        """Find a record (only within current tenant's data)."""
        tenant = TenantContext.require_current()
        key = f"{tenant.tenant_id}:{record_id}"
        if collection in self._data:
            return self._data[collection].get(key)
        return None

    def find_all(self, collection: str) -> list[Record]:
        """Find all records in collection (only current tenant's)."""
        tenant = TenantContext.require_current()
        if collection not in self._data:
            return []
        return [
            r
            for r in self._data[collection].values()
            if r.tenant_id == tenant.tenant_id
        ]

    def delete(self, collection: str, record_id: str) -> bool:
        """Delete a record (only if belongs to current tenant)."""
        tenant = TenantContext.require_current()
        key = f"{tenant.tenant_id}:{record_id}"
        if collection in self._data and key in self._data[collection]:
            del self._data[collection][key]
            self._usage[tenant.tenant_id] = max(
                0, self._usage.get(tenant.tenant_id, 0) - 1
            )
            return True
        return False

    def count(self, collection: str) -> int:
        """Count records in collection (only current tenant's)."""
        tenant = TenantContext.require_current()
        if collection not in self._data:
            return 0
        return sum(
            1
            for r in self._data[collection].values()
            if r.tenant_id == tenant.tenant_id
        )

    def get_tenant_usage(self, tenant_id: str) -> int:
        """Admin: get total records for a tenant."""
        return self._usage.get(tenant_id, 0)

    def get_all_records_admin(self, collection: str) -> list[Record]:
        """Admin: get ALL records (cross-tenant, for debugging)."""
        if collection not in self._data:
            return []
        return list(self._data[collection].values())
