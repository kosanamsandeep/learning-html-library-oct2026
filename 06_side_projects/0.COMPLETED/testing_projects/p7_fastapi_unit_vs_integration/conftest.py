"""Shared fixtures: a TestClient with an isolated ItemStore per test."""

import pytest
from fastapi.testclient import TestClient

from main import ItemService, ItemStore, app, get_service


@pytest.fixture
def store() -> ItemStore:
    return ItemStore()


@pytest.fixture
def service(store: ItemStore) -> ItemService:
    return ItemService(store)


@pytest.fixture
def client(service: ItemService) -> TestClient:
    """A FastAPI TestClient wired to a fresh service for each test."""
    app.dependency_overrides[get_service] = lambda: service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
