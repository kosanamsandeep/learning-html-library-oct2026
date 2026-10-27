"""Answering: pass text snippets + actual image bytes to a VLM."""
from __future__ import annotations
import base64
import os
from pathlib import Path
from typing import Sequence

from openai import OpenAI

SYS = ("You are a multimodal grounded assistant. Answer using ONLY the "
       "provided sources (text snippets and image attachments). Cite each "
       "claim like [chunk_id]. If unsure, say you don't know.")


class MMGenerator:
    def __init__(self) -> None:
        self.model = os.getenv("VISION_MODEL", "gpt-5-vision")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),
                             base_url=os.getenv("LLM_BASE_URL"))

    def answer(self, question: str, hits: Sequence[dict]) -> str:
        content: list[dict] = [{"type": "text",
                                 "text": f"Question: {question}\n\nSources:"}]
        for h in hits:
            content.append({"type": "text",
                             "text": f"[{h['chunk_id']}] ({h['modality']}) {h['text']}"})
            if h["modality"] in ("image", "video") and h["media_uri"] \
                    and Path(h["media_uri"]).exists():
                b64 = base64.b64encode(Path(h["media_uri"]).read_bytes()).decode()
                content.append({"type": "image_url",
                                 "image_url": {"url": f"data:image/png;base64,{b64}"}})
        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": SYS},
                      {"role": "user", "content": content}],
            temperature=0.0,
        )
        return r.choices[0].message.content or ""
