"""Tiny URL shortener used as the E2E target.

POST /links  body: {"url": "https://example.com"}
                returns: {"code": "abc123", "short_url": ".../abc123"}
GET  /{code}  -> 302 redirect to the original url
GET  /stats   -> {"total": N}
"""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl


class LinkIn(BaseModel):
    url: HttpUrl


class LinkOut(BaseModel):
    code: str
    short_url: str


_links: dict[str, str] = {}


app = FastAPI(title="P8 URL Shortener")


@app.post("/links", response_model=LinkOut, status_code=201)
def create_link(payload: LinkIn) -> LinkOut:
    code = secrets.token_urlsafe(6)
    _links[code] = str(payload.url)
    return LinkOut(code=code, short_url=f"http://localhost/{code}")


@app.get("/{code}")
def follow(code: str):
    url = _links.get(code)
    if not url:
        raise HTTPException(status_code=404, detail="not found")
    return RedirectResponse(url=url, status_code=302)


@app.get("/stats")
def stats() -> dict[str, int]:
    return {"total": len(_links)}


@app.post("/_admin/reset")
def reset() -> dict[str, str]:
    """E2E helper. In production you would never expose this."""
    _links.clear()
    return {"status": "reset"}
