"""Pandas execution skill (async wrapper)."""
from __future__ import annotations

import asyncio
import textwrap
import pandas as pd

from core.config import settings


def _load_df() -> pd.DataFrame:
    return pd.read_csv(settings.csv_path)


async def run_python(code: str) -> str:
    """Execute pandas code against `df`. Set variable `result` to return a value."""
    def _run() -> str:
        try:
            df = _load_df()
            ns: dict = {"df": df, "pd": pd}
            exec(textwrap.dedent(code), {}, ns)  # noqa: S102 — sandboxed-ish
            return str(ns.get("result", "executed (no `result` variable set)"))[:1500]
        except Exception as exc:  # noqa: BLE001
            return f"python error: {exc}"
    return await asyncio.to_thread(_run)
