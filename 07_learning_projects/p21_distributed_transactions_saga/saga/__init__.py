"""
P21 - Distributed Transactions with the Saga Pattern
=====================================================
A small in-process toolkit for keeping several microservices consistent
without a single distributed (2PC) transaction.

Inspired by: Netflix, AWS Step Functions, NServiceBus, Debezium (Outbox)
Patterns: Choreographed Saga, Orchestrated Saga, Compensating Transaction,
          Transactional Outbox, Idempotency Keys, Saga State Machine
"""

from .choreography import EventBus, SagaEvent, Service
from .idempotency import IdempotencyStore
from .orchestrator import OrchestratedSaga, SagaStatus, SagaStep
from .outbox import OutboxDispatcher, OutboxRecord, OutboxStore

__all__ = [
    "EventBus",
    "SagaEvent",
    "Service",
    "IdempotencyStore",
    "OrchestratedSaga",
    "SagaStatus",
    "SagaStep",
    "OutboxDispatcher",
    "OutboxRecord",
    "OutboxStore",
]
