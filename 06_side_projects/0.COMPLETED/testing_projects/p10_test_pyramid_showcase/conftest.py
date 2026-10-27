"""Shared fixtures for every layer of the pyramid."""

import socket
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient

import main
from repository import ProductRepository
from service import CheckoutService

# ---- unit-layer helpers ---------------------------------------------------


@pytest.fixture
def fake_repo() -> MagicMock:
    """A mock repository for unit-testing the service in isolation."""
    return MagicMock(spec=ProductRepository)


# ---- integration-layer helpers -------------------------------------------


@pytest.fixture
def repo(tmp_path) -> ProductRepository:
    db = tmp_path / "shop.sqlite"
    r = ProductRepository(db)
    yield r
    r.close()


@pytest.fixture
def service(repo) -> CheckoutService:
    return CheckoutService(repo)


@pytest.fixture
def client(repo) -> TestClient:
    """FastAPI TestClient with the repo dependency overridden."""
    main.app.dependency_overrides[main.get_repo] = lambda: repo
    main.app.dependency_overrides[main.get_service] = lambda: CheckoutService(repo)
    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()


# ---- E2E-layer helpers ----------------------------------------------------


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_until_ready(url: str, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            r = httpx.get(url, timeout=1.0)
            if r.status_code < 500:
                return
        except Exception:
            pass
        time.sleep(0.1)
    raise RuntimeError(f"server not ready at {url}")


@pytest.fixture(scope="session")
def live_url(tmp_path_factory):
    """Boot a real uvicorn server for the E2E test, with a clean SQLite file."""
    db_file = tmp_path_factory.mktemp("e2e") / "shop.sqlite"
    port = _free_port()
    cwd = Path(__file__).parent
    env = {
        "P10_DB_PATH": str(db_file),
        "PATH": __import__("os").environ.get("PATH", ""),
    }
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(cwd),
        env=env,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        _wait_until_ready(f"{url}/docs")
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
