"""Unified multimodal index using ChromaDB. Captions + transcripts make
non-text modalities text-searchable; the original media URI is kept on the
metadata so the answering VLM can re-attach the actual file.
"""
from __future__ import annotations
import os
from typing import Sequence

import chromadb
from chromadb.utils import embedding_functions

from .ingest import MMChunk

COLLECTION = "multimodal_rag"


class MMIndex:
    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(
            path=os.getenv("CHROMA_DIR", "./chroma_store")
        )
        self.embed = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=os.getenv("EMBED_MODEL", "BAAI/bge-large-en-v1.5"))
        self.col = self.client.get_or_create_collection(
            COLLECTION, embedding_function=self.embed)

    def add(self, chunks: Sequence[MMChunk]) -> None:
        if not chunks:
            return
        self.col.add(
            ids=[c.chunk_id for c in chunks],
            documents=[c.text for c in chunks],
            metadatas=[{"asset_id": c.asset_id,
                        "modality": c.modality,
                        "media_uri": c.media_uri or ""}
                       for c in chunks],
        )

    def search(self, query: str, k: int = 6,
               modality: str | None = None) -> list[dict]:
        where = {"modality": modality} if modality else None
        res = self.col.query(query_texts=[query], n_results=k, where=where)
        out = []
        for i in range(len(res["ids"][0])):
            out.append({
                "chunk_id": res["ids"][0][i],
                "text": res["documents"][0][i],
                "modality": res["metadatas"][0][i]["modality"],
                "media_uri": res["metadatas"][0][i]["media_uri"],
                "distance": res["distances"][0][i],
            })
        return out
