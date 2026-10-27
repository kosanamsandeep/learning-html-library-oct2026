"""Skill: safe arithmetic via numexpr (async)."""
from __future__ import annotations

import asyncio
import numexpr


async def calculate(expression: str) -> str:
    """Evaluate an arithmetic expression off the event loop."""
    def _run() -> str:
        try:
            return str(numexpr.evaluate(expression.strip()).item())
        except Exception as exc:  # noqa: BLE001
            return f"calculator error: {exc}"
    return await asyncio.to_thread(_run)
