"""LLM-based translation. Preserves segment boundaries so timestamps stay aligned."""
from __future__ import annotations
import os
from typing import List

from openai import OpenAI

from .stt import TranscriptSegment

PROMPT = ("Translate the following segments from {src} to {tgt}. "
          "Keep one translation per segment, in the same order, "
          "as a JSON array of strings only.")


class Translator:
    def __init__(self) -> None:
        self.model = os.getenv("LLM_MODEL", "gpt-5")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),
                             base_url=os.getenv("LLM_BASE_URL"))

    def translate(self, segments: List[TranscriptSegment], target_lang: str
                   ) -> List[str]:
        if not segments:
            return []
        src = segments[0].language
        if src == target_lang:
            return [s.text for s in segments]
        joined = "\n".join(f"{i+1}. {s.text}" for i, s in enumerate(segments))
        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system",
                        "content": PROMPT.format(src=src, tgt=target_lang)},
                       {"role": "user", "content": joined}],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        import json
        data = json.loads(r.choices[0].message.content or "{}")
        # accept either {"translations":[...]} or a list
        items = data.get("translations") if isinstance(data, dict) else data
        if not isinstance(items, list) or len(items) != len(segments):
            # fallback: split by newline
            items = [r.choices[0].message.content or ""] * len(segments)
        return [str(x) for x in items]
