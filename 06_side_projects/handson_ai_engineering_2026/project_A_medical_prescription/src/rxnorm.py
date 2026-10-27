"""RxNorm validator - looks up drug names against the RxNav public API.

Production note: replace with an internal cache or local SQLite mirror of
RxNorm to avoid rate-limits.
"""
from __future__ import annotations
import logging
from typing import Optional
import httpx

log = logging.getLogger(__name__)
RXNAV_BASE = "https://rxnav.nlm.nih.gov/REST"


class RxNormValidator:
    def __init__(self, timeout: float = 5.0) -> None:
        self._client = httpx.Client(timeout=timeout, base_url=RXNAV_BASE)

    def lookup_cui(self, drug_name: str) -> Optional[str]:
        """Return the RxNorm CUI for the closest match, or None."""
        try:
            r = self._client.get("/approximateTerm.json",
                                 params={"term": drug_name, "maxEntries": 1})
            r.raise_for_status()
            cands = r.json().get("approximateGroup", {}).get("candidate", [])
            if not cands:
                return None
            return cands[0].get("rxcui")
        except Exception as e:  # network / parsing
            log.warning("RxNorm lookup failed for %s: %s", drug_name, e)
            return None

    def close(self) -> None:
        self._client.close()
