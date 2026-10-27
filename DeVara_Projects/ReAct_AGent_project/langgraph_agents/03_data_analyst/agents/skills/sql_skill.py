"""SQL skills (async)."""
from __future__ import annotations

import asyncio
import sqlite3
from langchain_core.tools import tool
from core.config import settings


@tool
async def list_tables(_: str = "") -> str:
    """List tables in the analyst SQLite DB."""
    def _run() -> str:
        with sqlite3.connect(settings.db_path) as conn:
            rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return ", ".join(r[0] for r in rows) or "no tables"
    return await asyncio.to_thread(_run)


@tool
async def describe_table(name: str = "data") -> str:
    """Describe a table: columns and 5 sample rows."""
    def _run() -> str:
        with sqlite3.connect(settings.db_path) as conn:
            cols = conn.execute(f"PRAGMA table_info({name})").fetchall()
            sample = conn.execute(f"SELECT * FROM {name} LIMIT 5").fetchall()
        cols_s = ", ".join(f"{c[1]}:{c[2]}" for c in cols)
        return f"columns=[{cols_s}]\nsample={sample}"
    return await asyncio.to_thread(_run)


@tool
async def run_sql(query: str) -> str:
    """Execute a SQLite SELECT query. Returns up to 50 rows."""
    def _run() -> str:
        try:
            with sqlite3.connect(settings.db_path) as conn:
                rows = conn.execute(query).fetchmany(50)
            return str(rows) if rows else "no rows"
        except Exception as exc:  # noqa: BLE001
            return f"sql error: {exc}"
    return await asyncio.to_thread(_run)
