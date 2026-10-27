"""
P20 - Microservice Chassis: Service Registry & Discovery
=========================================================
Client-side service discovery with heartbeats and load balancing.
Inspired by: Consul, Eureka, etcd, Kubernetes Service Discovery.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from enum import Enum
from datetime import datetime
import time
import random
import hashlib


class ServiceStatus(Enum):
    """Coordinates business logic and keeps the calling code focused on use cases instead of implementation details."""
    REGISTERED = "registered"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEREGISTERED = "deregistered"


class LoadBalanceStrategy(Enum):
    """Implements one interchangeable algorithm behind a common interface."""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    CONSISTENT_HASH = "consistent_hash"


@dataclass
class ServiceInstance:
    """A single instance of a registered service."""

    service_name: str
    instance_id: str
    host: str
    port: int
    metadata: dict = field(default_factory=dict)
    status: ServiceStatus = ServiceStatus.REGISTERED
    last_heartbeat: float = field(default_factory=time.time)
    connections: int = 0

    @property
    def address(self) -> str:
        """Perform the address step used by this project."""
        return f"{self.host}:{self.port}"


class ServiceRegistry:
    """
    In-process service registry with heartbeat-based health tracking.
    Provides service discovery and configurable load balancing.
    """

    def __init__(self, heartbeat_ttl_seconds: float = 30.0):
        """Initialize the object with the dependencies or starting values it needs."""
        self._services: dict[str, dict[str, ServiceInstance]] = {}
        self._heartbeat_ttl = heartbeat_ttl_seconds
        self._round_robin_index: dict[str, int] = {}

    # ── Registration ──────────────────────────────────────────
    def register(
        self,
        service_name: str,
        instance_id: str,
        host: str,
        port: int,
        metadata: dict | None = None,
    ) -> ServiceInstance:
        """Register a service instance."""
        instance = ServiceInstance(
            service_name=service_name,
            instance_id=instance_id,
            host=host,
            port=port,
            metadata=metadata or {},
            status=ServiceStatus.HEALTHY,
        )
        self._services.setdefault(service_name, {})[instance_id] = instance
        return instance

    def deregister(self, service_name: str, instance_id: str) -> bool:
        """Remove a service instance."""
        instances = self._services.get(service_name, {})
        if instance_id in instances:
            instances[instance_id].status = ServiceStatus.DEREGISTERED
            del instances[instance_id]
            return True
        return False

    # ── Heartbeat ─────────────────────────────────────────────
    def heartbeat(self, service_name: str, instance_id: str) -> bool:
        """Update heartbeat timestamp for an instance."""
        instances = self._services.get(service_name, {})
        if instance_id in instances:
            instances[instance_id].last_heartbeat = time.time()
            instances[instance_id].status = ServiceStatus.HEALTHY
            return True
        return False

    def check_health(self) -> dict[str, list[str]]:
        """Check all instances for expired heartbeats."""
        now = time.time()
        unhealthy = {}
        for svc_name, instances in self._services.items():
            for inst_id, inst in instances.items():
                if now - inst.last_heartbeat > self._heartbeat_ttl:
                    inst.status = ServiceStatus.UNHEALTHY
                    unhealthy.setdefault(svc_name, []).append(inst_id)
        return unhealthy

    # ── Discovery ─────────────────────────────────────────────
    def get_instances(
        self, service_name: str, healthy_only: bool = True
    ) -> list[ServiceInstance]:
        """Get all instances of a service."""
        instances = self._services.get(service_name, {})
        if healthy_only:
            return [i for i in instances.values() if i.status == ServiceStatus.HEALTHY]
        return list(instances.values())

    def get_services(self) -> list[str]:
        """List all registered service names."""
        return list(self._services.keys())

    # ── Load Balancing ────────────────────────────────────────
    def resolve(
        self,
        service_name: str,
        strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN,
        key: str | None = None,
    ) -> ServiceInstance | None:
        """Resolve a single instance using the specified strategy."""
        instances = self.get_instances(service_name, healthy_only=True)
        if not instances:
            return None

        if strategy == LoadBalanceStrategy.ROUND_ROBIN:
            idx = self._round_robin_index.get(service_name, 0)
            instance = instances[idx % len(instances)]
            self._round_robin_index[service_name] = idx + 1
            return instance

        elif strategy == LoadBalanceStrategy.RANDOM:
            return random.choice(instances)

        elif strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return min(instances, key=lambda i: i.connections)

        elif strategy == LoadBalanceStrategy.CONSISTENT_HASH:
            if not key:
                return instances[0]
            hash_val = int(hashlib.md5(key.encode()).hexdigest(), 16)
            return instances[hash_val % len(instances)]

        return instances[0]
