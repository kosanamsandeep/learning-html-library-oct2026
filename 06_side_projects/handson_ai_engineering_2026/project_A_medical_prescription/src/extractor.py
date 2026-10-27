"""Vision-LLM client for prescription images.

Uses OpenAI-compatible structured outputs (works with GPT-5, GPT-4o, Mistral
Large 3, Gemini-3-Pro via LiteLLM proxy). The Pydantic schema is passed via
`response_format` so the model returns guaranteed-valid JSON.
"""
from __future__ import annotations
import base64
import os
from pathlib import Path
from typing import Union

from openai import OpenAI

from .schemas import Prescription

SYSTEM_PROMPT = """You are a clinical OCR assistant. Read the prescription image
and extract every medication exactly as written. Preserve the original drug name
spelling - do NOT auto-correct. If a field is unreadable, leave it null. Estimate
your overall extraction confidence between 0 and 1.
"""


class PrescriptionExtractor:
    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("VISION_MODEL", "gpt-5-vision")
        self._client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
        )

    @staticmethod
    def _to_data_url(image: Union[str, Path, bytes]) -> str:
        if isinstance(image, (str, Path)):
            data = Path(image).read_bytes()
        else:
            data = image
        b64 = base64.b64encode(data).decode()
        return f"data:image/png;base64,{b64}"

    def extract(self, image: Union[str, Path, bytes]) -> Prescription:
        data_url = self._to_data_url(image)
        completion = self._client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": "Extract this prescription as JSON."},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ]},
            ],
            response_format=Prescription,
            temperature=0.0,
        )
        return completion.choices[0].message.parsed
