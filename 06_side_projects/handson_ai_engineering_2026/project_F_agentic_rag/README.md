# Project F · Self-Reflective Agentic RAG (LangGraph)

A stateful, looping RAG that grades its own retrieval, groundedness and answer quality, and rewrites the query when checks fail.

```bash
pip install -r requirements.txt
cp .env.example .env
python -m src.cli --ingest ./data --ask "What did the report say about Q4 churn?"
```
