"""Tests for P6 — illustrates dependency_overrides + httpx.AsyncClient against ASGI."""

import pytest
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        r = await ac.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_and_get_widget():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        r = await ac.post("/widgets", json={"name": "blue widget"})
        assert r.status_code == 201
        wid = r.json()["id"]

        r2 = await ac.get(f"/widgets/{wid}")
        assert r2.status_code == 200
        assert r2.json()["name"] == "blue widget"


@pytest.mark.asyncio
async def test_widget_not_found_returns_uniform_shape():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        r = await ac.get("/widgets/does-not-exist")
    assert r.status_code == 404
    body = r.json()
    assert body["error"] == "not_found"
    assert "widget" in body["detail"]
