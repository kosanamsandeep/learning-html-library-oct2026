"""Async wikipedia summary skill."""
from __future__ import annotations
import asyncio
import wikipedia
from langchain_core.tools import tool


@tool
async def wiki(query: str) -> str:
    """Return a 3-sentence Wikipedia summary for `query`."""
    def _run() -> str:
        try:
            return wikipedia.summary(query, sentences=3, auto_suggest=True)
        except wikipedia.DisambiguationError as exc:
            return f"ambiguous, options: {exc.options[:5]}"
        except Exception as exc:  # noqa: BLE001
            return f"wiki error: {exc}"
    return await asyncio.to_thread(_run)
