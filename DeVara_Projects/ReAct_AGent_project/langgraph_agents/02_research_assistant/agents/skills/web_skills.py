"""Reusable async skills (no LangChain Tool wrapper — graph nodes call them directly)."""
from __future__ import annotations

import asyncio
import re

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


async def web_search(query: str, max_results: int = 3) -> list[str]:
    def _run() -> list[str]:
        try:
            with DDGS() as ddgs:
                return [r["href"] for r in ddgs.text(query, max_results=max_results)]
        except Exception:  # noqa: BLE001
            return []
    return await asyncio.to_thread(_run)


async def read_url(url: str, max_chars: int = 2500) -> str:
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True,
                                     headers={"User-Agent": "Mozilla/5.0"}) as c:
            r = await c.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script", "style", "nav", "footer", "header"]):
            t.decompose()
        return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))[:max_chars]
    except Exception as exc:  # noqa: BLE001
        return f"(read error: {exc})"
