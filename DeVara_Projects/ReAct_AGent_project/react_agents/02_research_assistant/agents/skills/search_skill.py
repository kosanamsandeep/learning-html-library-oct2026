"""Async DuckDuckGo web search."""
from __future__ import annotations

import asyncio
from duckduckgo_search import DDGS


async def web_search(query: str, max_results: int = 5) -> str:
    def _run() -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            return "\n".join(f"- {r['title']} — {r['href']}" for r in results) or "no results"
        except Exception as exc:  # noqa: BLE001
            return f"search error: {exc}"
    return await asyncio.to_thread(_run)
