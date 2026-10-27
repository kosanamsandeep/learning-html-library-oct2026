"""Modality-aware ingestion for a unified multimodal index.

Strategy:
  text   -> plain text chunks
  image  -> ColPali-style page embeddings (here: CLIP fallback)
  audio  -> faster-whisper transcript -> text chunks
  video  -> keyframes (OpenCV) + audio track -> image + text

Embeddings are stored in ChromaDB with `modality` metadata so we can
optionally route by modality at query time.
"""
from __future__ import annotations
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

log = logging.getLogger(__name__)
Modality = Literal["text", "image", "audio", "video"]


@dataclass
class MMChunk:
    asset_id: str         # original file path or URL
    chunk_id: str
    modality: Modality
    text: str             # text or caption (for retrieval)
    media_uri: str | None  # path to image / audio segment for the LLM


# ---------- text ----------
def _text(path: Path) -> Iterable[MMChunk]:
    body = path.read_text(encoding="utf-8")
    for i, para in enumerate(body.split("\n\n")):
        if para.strip():
            yield MMChunk(str(path), f"{path.name}::p{i}", "text", para.strip(), None)


# ---------- image ----------
def _image(path: Path) -> Iterable[MMChunk]:
    """Caption the image with a VLM so it becomes searchable text."""
    try:
        from openai import OpenAI
        import base64
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),
                        base_url=os.getenv("LLM_BASE_URL"))
        b64 = base64.b64encode(path.read_bytes()).decode()
        r = client.chat.completions.create(
            model=os.getenv("VISION_MODEL", "gpt-5-vision"),
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "Describe this image in 2-3 sentences. "
                                          "Include any text visible."},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
            temperature=0.0,
        )
        caption = r.choices[0].message.content or ""
    except Exception as e:
        log.warning("VLM caption failed for %s: %s", path, e)
        caption = f"image {path.name}"
    yield MMChunk(str(path), f"{path.name}::img", "image", caption, str(path))


# ---------- audio ----------
def _audio(path: Path) -> Iterable[MMChunk]:
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(os.getenv("WHISPER_MODEL", "base"), device="auto")
        segs, _ = model.transcribe(str(path), vad_filter=True)
        for i, s in enumerate(segs):
            yield MMChunk(str(path), f"{path.name}::s{i}", "audio",
                          s.text.strip(), str(path))
    except Exception as e:
        log.warning("audio transcription failed for %s: %s", path, e)
        yield MMChunk(str(path), f"{path.name}::raw", "audio",
                      f"audio file {path.name}", str(path))


# ---------- video ----------
def _video(path: Path) -> Iterable[MMChunk]:
    """Extract keyframes + audio track, then reuse _image / _audio."""
    try:
        import cv2
        cap = cv2.VideoCapture(str(path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        every_n = int(fps * 5)  # 1 keyframe / 5s
        i = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if i % every_n == 0:
                kf = path.with_suffix(f".kf{i}.jpg")
                cv2.imwrite(str(kf), frame)
                yield from _image(kf)
            i += 1
        cap.release()
    except Exception as e:
        log.warning("video processing failed for %s: %s", path, e)


# ---------- dispatcher ----------
EXT_MAP = {
    ".txt": _text, ".md": _text,
    ".png": _image, ".jpg": _image, ".jpeg": _image, ".webp": _image,
    ".mp3": _audio, ".wav": _audio, ".m4a": _audio,
    ".mp4": _video, ".mov": _video, ".mkv": _video,
}


def ingest_folder(folder: str | Path) -> Iterable[MMChunk]:
    folder = Path(folder)
    for f in folder.rglob("*"):
        if f.is_file() and f.suffix.lower() in EXT_MAP:
            yield from EXT_MAP[f.suffix.lower()](f)
