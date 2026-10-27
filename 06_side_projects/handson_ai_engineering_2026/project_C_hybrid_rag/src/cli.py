"""CLI entry: ingest a folder, then ask questions interactively."""
from __future__ import annotations
import argparse
import logging

from .generator import Generator
from .loaders import load_documents
from .retriever import HybridIndex


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ingest", help="folder of .txt files to index")
    p.add_argument("--ask", help="question to ask after indexing")
    p.add_argument("--k", type=int, default=5)
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO)
    idx = HybridIndex()
    gen = Generator()

    if args.ingest:
        chunks = list(load_documents(args.ingest))
        logging.info("Loaded %d chunks", len(chunks))
        idx.build(chunks)

    if args.ask:
        hits = idx.search(args.ask, k=args.k)
        print("\n--- Top sources ---")
        for h in hits:
            print(f"[{h.chunk_id}] score={h.score:.3f}")
        print("\n--- Answer ---")
        print(gen.answer(args.ask, hits))


if __name__ == "__main__":
    main()
