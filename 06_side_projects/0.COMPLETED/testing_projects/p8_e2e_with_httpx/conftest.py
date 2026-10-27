"""Session-scoped fixture: start a real uvicorn server in a subprocess.

This is what makes the tests truly end-to-end. We are not calling the app
in-process like P7. We boot it as a separate process and talk to it over HTTP.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_until_ready(url: str, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            r = httpx.get(url, timeout=1.0)
            if r.status_code < 500:
                return
        except Exception as exc:  # noqa: BLE001 -- broad on purpose during boot
            last_error = exc
        time.sleep(0.1)
    raise RuntimeError(f"server at {url} did not start in time: {last_error}")


@pytest.fixture(scope="session")
def base_url():
    port = _free_port()
    cwd = Path(__file__).parent
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
    )
    url = f"http://127.0.0.1:{port}"
    try:
        _wait_until_ready(f"{url}/stats")
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture
def client(base_url):
    """Fresh httpx client per test; reset server state before each test."""
    with httpx.Client(base_url=base_url, follow_redirects=False) as c:
        c.post("/_admin/reset")
        yield c
