"""Pandas + chart skills (async)."""
from __future__ import annotations

import asyncio
import datetime as _dt
import textwrap
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from langchain_core.tools import tool
from core.config import settings


@tool
async def run_python(code: str) -> str:
    """Run pandas code on `df` (the loaded CSV). Set `result` variable to return a value."""
    def _run() -> str:
        try:
            df = pd.read_csv(settings.csv_path)
            ns: dict = {"df": df, "pd": pd}
            exec(textwrap.dedent(code), {}, ns)  # noqa: S102
            return str(ns.get("result", "executed (set `result`)"))[:1500]
        except Exception as exc:  # noqa: BLE001
            return f"python error: {exc}"
    return await asyncio.to_thread(_run)


@tool
async def make_chart(spec: str) -> str:
    """Render a chart. spec format: 'kind|x|y[|groupby]', kind in {bar,line,barh,pie}."""
    def _run() -> str:
        try:
            parts = [p.strip() for p in spec.split("|")]
            kind, x, y = parts[0], parts[1], parts[2]
            group = parts[3] if len(parts) > 3 else None
            df = pd.read_csv(settings.csv_path)
            settings.charts_dir.mkdir(parents=True, exist_ok=True)
            fig, ax = plt.subplots(figsize=(7, 4))
            if group:
                df.pivot_table(index=x, columns=group, values=y, aggfunc="sum").plot(kind=kind, ax=ax)
            else:
                df.groupby(x)[y].sum().plot(kind=kind, ax=ax)
            ax.set_title(f"{y} by {x}" + (f" (by {group})" if group else ""))
            ts = _dt.datetime.now().strftime("%H%M%S")
            path = settings.charts_dir / f"chart_{ts}.png"
            fig.tight_layout()
            fig.savefig(path)
            plt.close(fig)
            return str(path)
        except Exception as exc:  # noqa: BLE001
            return f"chart error: {exc}"
    return await asyncio.to_thread(_run)
