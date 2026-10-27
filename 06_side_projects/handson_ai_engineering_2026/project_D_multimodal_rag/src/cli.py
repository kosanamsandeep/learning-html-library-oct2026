"""CLI for multimodal RAG."""
from __future__ import annotations
import argparse
import logging

from .generator import MMGenerator
from .index import MMIndex
from .ingest import ingest_folder


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ingest", help="folder of mixed-modality assets")
    p.add_argument("--ask", help="question after indexing")
    p.add_argument("--modality", choices=["text", "image", "audio", "video"],
                    help="optional modality filter")
    p.add_argument("--k", type=int, default=6)
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO)
    idx, gen = MMIndex(), MMGenerator()

    if args.ingest:
        chunks = list(ingest_folder(args.ingest))
        logging.info("Ingested %d chunks", len(chunks))
        idx.add(chunks)

    if args.ask:
        hits = idx.search(args.ask, k=args.k, modality=args.modality)
        for h in hits:
            print(f"[{h['chunk_id']}] {h['modality']:5s} d={h['distance']:.3f}")
        print("\n--- Answer ---")
        print(gen.answer(args.ask, hits))


if __name__ == "__main__":
    main()
