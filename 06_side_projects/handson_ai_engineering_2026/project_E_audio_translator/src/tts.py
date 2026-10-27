"""Text-to-speech using Kokoro (open weights) or OpenAI tts as fallback."""
from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Iterable

log = logging.getLogger(__name__)


class TTS:
    def __init__(self, prefer_kokoro: bool = True) -> None:
        self.prefer_kokoro = prefer_kokoro
        self._kokoro = None
        if prefer_kokoro:
            try:
                from kokoro import KPipeline  # pip install kokoro
                self._kokoro = KPipeline(
                    lang_code=os.getenv("TTS_LANG", "en-us"))
            except Exception as e:
                log.warning("Kokoro unavailable, will fallback to OpenAI: %s", e)

    def synthesize(self, segments: Iterable[str], out_path: str) -> str:
        text = " ".join(segments)
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if self._kokoro:
            import soundfile as sf
            audio_chunks = []
            for _, _, audio in self._kokoro(text, voice=os.getenv("TTS_VOICE", "af_heart")):
                audio_chunks.append(audio)
            import numpy as np
            arr = np.concatenate(audio_chunks)
            sf.write(out, arr, 24000)
            return str(out)
        # fallback: OpenAI
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),
                        base_url=os.getenv("LLM_BASE_URL"))
        with client.audio.speech.with_streaming_response.create(
                model=os.getenv("TTS_MODEL", "gpt-4o-mini-tts"),
                voice=os.getenv("TTS_VOICE", "alloy"),
                input=text) as r:
            r.stream_to_file(str(out))
        return str(out)
