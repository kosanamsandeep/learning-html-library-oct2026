"""Async calculator skill — same as ReAct version."""
from __future__ import annotations
import asyncio
import numexpr
from langchain_core.tools import tool


@tool
async def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression like '23*45+1'."""
    def _run() -> str:
        try:
            return str(numexpr.evaluate(expression.strip()).item())
        except Exception as exc:  # noqa: BLE001
            return f"calculator error: {exc}"
    return await asyncio.to_thread(_run)
