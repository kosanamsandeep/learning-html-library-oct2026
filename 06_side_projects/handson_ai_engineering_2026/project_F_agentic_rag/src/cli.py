"""CLI for the self-reflective agentic RAG."""
from __future__ import annotations
import argparse
import logging

from .graph import build_graph
from .retriever import SimpleRetriever


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ingest", required=True)
    p.add_argument("--ask", required=True)
    a = p.parse_args()

    logging.basicConfig(level=logging.INFO)
    r = SimpleRetriever()
    r.from_folder(a.ingest)
    app = build_graph(r)
    state = app.invoke({"question": a.ask, "iterations": 0,
                         "docs": [], "messages": []})
    print("\n=== Final answer ===")
    print(state.get("answer") or "(no answer produced)")
    print(f"\niterations={state['iterations']}  "
          f"grounded={state.get('grounded_ok')}  "
          f"quality={state.get('quality_ok')}")


if __name__ == "__main__":
    main()
