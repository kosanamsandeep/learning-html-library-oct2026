"""SQLite skill — async wrapper around a pandas-loaded DB."""
from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from core.config import settings


async def list_tables(_: str = "") -> str:
    def _run() -> str:
        with sqlite3.connect(settings.db_path) as conn:
            rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return ", ".join(r[0] for r in rows) or "no tables"
    return await asyncio.to_thread(_run)


async def describe_table(name: str) -> str:
    name = (name or "data").strip()
    def _run() -> str:
        with sqlite3.connect(settings.db_path) as conn:
            cols = conn.execute(f"PRAGMA table_info({name})").fetchall()
            sample = conn.execute(f"SELECT * FROM {name} LIMIT 5").fetchall()
        cols_s = ", ".join(f"{c[1]}:{c[2]}" for c in cols)
        return f"columns=[{cols_s}]\nsample_rows={sample}"
    return await asyncio.to_thread(_run)


async def run_sql(sql: str) -> str:
    def _run() -> str:
        try:
            with sqlite3.connect(settings.db_path) as conn:
                rows = conn.execute(sql).fetchmany(50)
            return str(rows) if rows else "no rows"
        except Exception as exc:  # noqa: BLE001
            return f"sql error: {exc}"
    return await asyncio.to_thread(_run)
