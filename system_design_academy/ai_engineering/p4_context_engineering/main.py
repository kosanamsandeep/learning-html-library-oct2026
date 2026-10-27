"""P4 AI Engineering · Context Engineering.

Every LLM call has a token budget. Naively concatenating chat history,
retrieved docs, and tool outputs blows past that budget. *Context
engineering* is the discipline of picking, ordering, and compressing the
right pieces so the model sees what matters and nothing else.

This file implements:
  - A token budget (we approximate 1 token ≈ 4 chars for the demo).
  - Retrieval merge with deduplication.
  - Recency + relevance weighting.
  - Two compression strategies: truncation and extractive summary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


def tokens(text: str) -> int:
    """Rough token count: ~4 characters per token."""
    return max(1, len(text) // 4)


@dataclass
class Chunk:
    """One retrievable unit of context."""

    text: str
    source: str
    score: float = 0.0  # relevance to the current query
    recency: float = 1.0  # 1.0 = newest, decays over time


@dataclass
class ContextBudget:
    """Pick chunks under `max_tokens`, ordered by combined score."""

    max_tokens: int

    @staticmethod
    def _key(chunk: Chunk) -> float:
        """Combine relevance and recency into one ranking score."""
        return 0.7 * chunk.score + 0.3 * chunk.recency

    def fit(self, chunks: list[Chunk]) -> list[Chunk]:
        """Greedy pack: highest combined score first, until the budget runs out."""
        ordered = sorted(chunks, key=self._key, reverse=True)
        picked: list[Chunk] = []
        used = 0
        for c in ordered:
            t = tokens(c.text)
            if used + t > self.max_tokens:
                continue
            picked.append(c)
            used += t
        return picked


def dedupe(chunks: list[Chunk]) -> list[Chunk]:
    """Drop chunks whose text is a near-duplicate of an earlier chunk."""
    seen: set[str] = set()
    out: list[Chunk] = []
    for c in chunks:
        fingerprint = re.sub(r"\s+", " ", c.text.lower())[:80]
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        out.append(c)
    return out


def truncate(text: str, max_chars: int) -> str:
    """Cut a string to `max_chars` and add an ellipsis."""
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


def summarize_extractive(text: str, keep_sentences: int = 2) -> str:
    """Tiny extractive summary: keep first N sentences."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(parts[:keep_sentences])


# ---------- demo --------------------------------------------------------


def main() -> None:
    """Show retrieve → dedupe → compress → budget-fit pipeline."""
    candidates = [
        Chunk(
            "Bengaluru is the capital of Karnataka and a major tech hub.",
            "wiki",
            0.9,
            0.4,
        ),
        Chunk(
            "Bengaluru is the capital of Karnataka and a major tech hub.",
            "blog",
            0.7,
            0.9,
        ),  # dup
        Chunk(
            "Apartment rentals in Bengaluru have risen by 25% since 2022. Tech salaries "
            "have grown as well. Many companies have moved to hybrid work. The city's "
            "metro has expanded to support more areas.",
            "news",
            0.85,
            0.95,
        ),
        Chunk(
            "Bengaluru weather is mild year round with monsoon from June to September.",
            "wiki",
            0.4,
            0.5,
        ),
        Chunk(
            "Coffee culture in Bengaluru is strong; many third-wave cafes opened recently.",
            "blog",
            0.2,
            0.99,
        ),
    ]

    print("--- raw candidates ---")
    for c in candidates:
        print(
            f"  score={c.score:.2f} recency={c.recency:.2f} t={tokens(c.text):3d}  src={c.source:5s}  {truncate(c.text, 60)}"
        )

    deduped = dedupe(candidates)
    print(f"\n--- after dedupe: {len(deduped)} chunks ---")

    # Compress the long news chunk before budgeting.
    for c in deduped:
        if tokens(c.text) > 40:
            c.text = summarize_extractive(c.text, keep_sentences=2)
            print(f"  compressed: {c.source} -> {c.text}")

    picked = ContextBudget(max_tokens=40).fit(deduped)
    print(
        f"\n--- picked under 40 tokens ({sum(tokens(c.text) for c in picked)} used) ---"
    )
    for c in picked:
        print(f"  src={c.source:5s}  {c.text}")


if __name__ == "__main__":
    main()
