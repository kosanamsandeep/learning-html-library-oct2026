"""End-to-end speech-to-speech pipeline: stt -> translate -> tts."""
from __future__ import annotations
import argparse
import logging

from .stt import Transcriber
from .translate import Translator
from .tts import TTS


def run(input_audio: str, target_lang: str, out_audio: str) -> None:
    t = Transcriber()
    tr = Translator()
    speaker = TTS()

    src_lang, segs = t.transcribe(input_audio)
    print(f"[STT] detected {src_lang}, {len(segs)} segments")
    translated = tr.translate(segs, target_lang)
    for s, x in zip(segs, translated):
        print(f"  {s.start:6.2f}->{s.end:6.2f}  {s.text!r}\n            -> {x!r}")
    speaker.synthesize(translated, out_audio)
    print(f"[TTS] wrote {out_audio}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--to", required=True, help="target language code, e.g. es, de, fr")
    p.add_argument("--out", default="./out.wav")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO)
    run(a.input, a.to, a.out)


if __name__ == "__main__":
    main()
