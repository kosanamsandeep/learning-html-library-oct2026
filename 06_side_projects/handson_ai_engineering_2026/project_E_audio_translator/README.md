# Project E · Multilingual Audio Translator

Speech-in → translate → speech-out using **faster-whisper + GPT-5 + Kokoro TTS**.

```bash
pip install -r requirements.txt
cp .env.example .env
python -m src.pipeline ./samples/hindi.mp3 --to en --out ./out.wav
```
