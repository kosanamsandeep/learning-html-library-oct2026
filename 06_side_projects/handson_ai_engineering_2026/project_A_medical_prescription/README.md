# Project A · Medical Prescription Digitizer

End-to-end pipeline that turns a photo of a hand-written or printed prescription
into a **validated, structured record** persisted in SQLite.

## Stack (2026)
- Vision-LLM with native structured-output (`response_format=Pydantic`)
- Pydantic v2 schemas (typed enums for frequency / route)
- RxNorm via `rxnav.nlm.nih.gov` for drug-name validation
- SQLite persistence (3-table ERD)

## Quick start
```bash
pip install -r requirements.txt
cp .env.example .env  # add OPENAI_API_KEY
python -m src.pipeline samples/rx1.png samples/rx2.jpg
```

See `architecture.html` for full design, ERD and 2026 technique notes.
