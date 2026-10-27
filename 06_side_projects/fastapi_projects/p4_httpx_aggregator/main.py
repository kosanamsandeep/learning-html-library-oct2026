"""
P4 — FastAPI + httpx aggregator.

The classic "BFF for Frontend" pattern:
    GitHub user + their repos + their followers, in ONE response, with ONE round trip
    from the client. We call the 3 upstream endpoints concurrently with
    `asyncio.gather` so the total wait is ~ the slowest single call, not the sum.

Notice:
  * ONE AsyncClient created in lifespan, reused for the app's lifetime.
  * Strict timeouts.
  * Graceful handling of partial failure: if one upstream errors, the others still return.
"""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request

GITHUB = "https://api.github.com"


@asynccontextmanager
async def lifespan(app: FastAPI):
    timeout = httpx.Timeout(5.0, connect=2.0)
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
    app.state.http = httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "fastapi-aggregator",
        },
        http2=False,  # set True if you `pip install h2`
    )
    yield
    await app.state.http.aclose()


app = FastAPI(
    title="GitHub Aggregator",
    version="1.0.0",
    description="Fetch a GitHub user + their repos + their followers concurrently.",
    lifespan=lifespan,
)


async def _safe_get_json(client: httpx.AsyncClient, url: str) -> Any:
    """Call upstream, return parsed JSON or a structured error dict (never raise)."""
    try:
        r = await client.get(url)
        if r.status_code == 404:
            return {"_error": "not_found", "url": url}
        r.raise_for_status()
        return r.json()
    except httpx.TimeoutException:
        return {"_error": "timeout", "url": url}
    except httpx.HTTPError as e:
        return {"_error": "http_error", "url": url, "detail": str(e)}


@app.get("/github/{username}", tags=["aggregator"])
async def github_profile(username: str, request: Request) -> dict[str, Any]:
    """
    One call from the client → three concurrent calls upstream → one merged response.
    Wall-clock time is ~ the slowest single upstream, not the sum.
    """
    client: httpx.AsyncClient = request.app.state.http

    started = time.perf_counter()
    user, repos, followers = await asyncio.gather(
        _safe_get_json(client, f"{GITHUB}/users/{username}"),
        _safe_get_json(
            client, f"{GITHUB}/users/{username}/repos?per_page=5&sort=updated"
        ),
        _safe_get_json(client, f"{GITHUB}/users/{username}/followers?per_page=5"),
    )
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    if isinstance(user, dict) and user.get("_error") == "not_found":
        raise HTTPException(
            status_code=404, detail=f"GitHub user '{username}' not found"
        )

    return {
        "username": username,
        "elapsed_ms_concurrent": elapsed_ms,
        "user": user,
        "repos": repos,
        "followers": followers,
    }


@app.get("/github-sequential/{username}", tags=["aggregator"])
async def github_profile_sequential(username: str, request: Request) -> dict[str, Any]:
    """The SAME work, done one after the other — for comparison. Should be ~3x slower."""
    client: httpx.AsyncClient = request.app.state.http
    started = time.perf_counter()
    user = await _safe_get_json(client, f"{GITHUB}/users/{username}")
    repos = await _safe_get_json(
        client, f"{GITHUB}/users/{username}/repos?per_page=5&sort=updated"
    )
    followers = await _safe_get_json(
        client, f"{GITHUB}/users/{username}/followers?per_page=5"
    )
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return {
        "username": username,
        "elapsed_ms_sequential": elapsed_ms,
        "user": user,
        "repos": repos,
        "followers": followers,
    }
