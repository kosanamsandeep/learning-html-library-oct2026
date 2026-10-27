"""Async file-saving skill."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
import aiofiles
from core.config import settings


async def save_report(content: str) -> str:
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    path: Path = settings.reports_dir / f"report_{ts}.md"
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content)
    return str(path)
