"""Generation step: grounded answer with inline citations."""
from __future__ import annotations
import os
from typing import Sequence

from openai import OpenAI

from .retriever import Hit

PROMPT = """You are a factual assistant. Answer the question using ONLY the
sources below. Cite each claim like [doc_id::chunk_idx]. If the answer is not
in the sources, say "I don't know based on the provided documents."

Question: {q}

Sources:
{ctx}
"""


def _format_sources(hits: Sequence[Hit]) -> str:
    return "\n\n".join(f"[{h.chunk_id}] {h.text}" for h in hits)


class Generator:
    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("LLM_MODEL", "gpt-5")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),
                             base_url=os.getenv("LLM_BASE_URL"))

    def answer(self, question: str, hits: Sequence[Hit]) -> str:
        prompt = PROMPT.format(q=question, ctx=_format_sources(hits))
        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        return r.choices[0].message.content or ""
