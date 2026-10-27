"""Document loading and semantic chunking (2026: late-chunking style)."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import re

@dataclass
class Chunk:
    doc_id: str
    chunk_id: str
    text: str
    section: str | None = None


def _split_sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def semantic_chunks(text: str, target_words: int = 220, overlap: int = 1) -> List[str]:
    """Greedy boundary-aware chunker. Production: replace with `chonkie` or
    Jina late-chunking for 2026 SOTA."""
    sents = _split_sentences(text)
    chunks, buf, words = [], [], 0
    for s in sents:
        w = len(s.split())
        if words + w > target_words and buf:
            chunks.append(" ".join(buf))
            buf = buf[-overlap:] if overlap else []
            words = sum(len(x.split()) for x in buf)
        buf.append(s)
        words += w
    if buf:
        chunks.append(" ".join(buf))
    return chunks


def load_documents(folder: str | Path) -> Iterable[Chunk]:
    folder = Path(folder)
    for f in folder.rglob("*.txt"):
        text = f.read_text(encoding="utf-8")
        for i, c in enumerate(semantic_chunks(text)):
            yield Chunk(doc_id=f.stem, chunk_id=f"{f.stem}::{i}", text=c)
