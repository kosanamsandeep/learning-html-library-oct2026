"""Speech-to-text using faster-whisper. Handles language auto-detection."""
from __future__ import annotations
import logging
import os
from dataclasses import dataclass
from typing import List

log = logging.getLogger(__name__)


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    language: str


class Transcriber:
    def __init__(self, model_size: str | None = None) -> None:
        from faster_whisper import WhisperModel
        self.model = WhisperModel(
            model_size or os.getenv("WHISPER_MODEL", "large-v3"),
            device="auto",
            compute_type="int8_float16",
        )

    def transcribe(self, path: str) -> tuple[str, List[TranscriptSegment]]:
        segs, info = self.model.transcribe(
            path, vad_filter=True, beam_size=5,
            condition_on_previous_text=False,
        )
        out = []
        for s in segs:
            out.append(TranscriptSegment(s.start, s.end, s.text.strip(),
                                          info.language))
        log.info("Detected lang=%s prob=%.2f", info.language,
                 info.language_probability)
        return info.language, out
