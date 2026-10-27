"""Lightweight in-memory retriever (BM25) for the demo.
Swap with the project_C HybridIndex in production.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from rank_bm25 import BM25Okapi

log = logging.getLogger(__name__)


@dataclass
class Doc:
    id: str
    text: str


class SimpleRetriever:
    def __init__(self) -> None:
        self.docs: list[Doc] = []
        self._bm25: BM25Okapi | None = None

    def index(self, docs: Sequence[Doc]) -> None:
        self.docs = list(docs)
        self._bm25 = BM25Okapi([d.text.lower().split() for d in self.docs])

    def from_folder(self, folder: str | Path) -> None:
        docs = []
        for f in Path(folder).rglob("*.txt"):
            text = f.read_text(encoding="utf-8")
            for i, p in enumerate(text.split("\n\n")):
                if p.strip():
                    docs.append(Doc(id=f"{f.stem}::{i}", text=p.strip()))
        log.info("indexed %d passages", len(docs))
        self.index(docs)

    def search(self, query: str, k: int = 4) -> List[Doc]:
        if not self._bm25:
            return []
        scores = self._bm25.get_scores(query.lower().split())
        ranked = sorted(enumerate(scores), key=lambda x: -x[1])[:k]
        return [self.docs[i] for i, _ in ranked]
