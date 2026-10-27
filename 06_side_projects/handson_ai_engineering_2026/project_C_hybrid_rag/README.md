# Project C · Hybrid RAG (Vector + BM25 + Rerank)

```bash
docker run -p 6333:6333 qdrant/qdrant   # one-time
pip install -r requirements.txt
cp .env.example .env
python -m src.cli --ingest ./data --ask "What is the policy on refunds?"
```
See `architecture.html` for diagrams + 2026 evaluation.
