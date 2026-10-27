"""Async URL reader that returns cleaned visible text."""
from __future__ import annotations

import re
import httpx
from bs4 import BeautifulSoup


async def read_url(url: str, max_chars: int = 4000) -> str:
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True,
                                     headers={"User-Agent": "Mozilla/5.0"}) as c:
            r = await c.get(url.strip())
            r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script", "style", "nav", "footer", "header"]):
            t.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        return text[:max_chars]
    except Exception as exc:  # noqa: BLE001
        return f"read error: {exc}"
