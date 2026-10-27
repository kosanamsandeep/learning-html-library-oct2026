"""Skill: Wikipedia summary lookup (async wrapper around blocking lib)."""
from __future__ import annotations

import asyncio
import wikipedia


async def wiki_summary(query: str, sentences: int = 3) -> str:
    def _run() -> str:
        try:
            return wikipedia.summary(query, sentences=sentences, auto_suggest=True)
        except wikipedia.DisambiguationError as exc:
            return f"ambiguous query, options: {exc.options[:5]}"
        except Exception as exc:  # noqa: BLE001
            return f"wiki error: {exc}"
    return await asyncio.to_thread(_run)
