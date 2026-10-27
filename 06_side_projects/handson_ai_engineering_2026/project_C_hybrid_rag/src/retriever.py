"""Hybrid retrieval: dense (Qdrant) + sparse (BM25) + RRF fusion + cross-encoder rerank."""
from __future__ import annotations
import math
import os
from dataclasses import dataclass
from typing import List, Sequence

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

from .loaders import Chunk

COLLECTION = "hybrid_rag"
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-large-en-v1.5")
RERANK_MODEL = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-v2-m3")


@dataclass
class Hit:
    chunk_id: str
    doc_id: str
    text: str
    score: float
    source: str  # "dense" | "bm25" | "rerank"


class HybridIndex:
    def __init__(self) -> None:
        self.embedder = SentenceTransformer(EMBED_MODEL)
        self.reranker = CrossEncoder(RERANK_MODEL)
        self.qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        self._chunks: list[Chunk] = []
        self._bm25: BM25Okapi | None = None

    # ---------------- ingest ----------------
    def build(self, chunks: Sequence[Chunk]) -> None:
        self._chunks = list(chunks)
        # 1) Dense
        vecs = self.embedder.encode([c.text for c in self._chunks],
                                    normalize_embeddings=True).tolist()
        dim = len(vecs[0])
        self.qdrant.recreate_collection(
            COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        self.qdrant.upsert(
            COLLECTION,
            points=[PointStruct(id=i, vector=v,
                                payload={"chunk_id": c.chunk_id,
                                         "doc_id": c.doc_id, "text": c.text})
                    for i, (c, v) in enumerate(zip(self._chunks, vecs))],
        )
        # 2) Sparse
        self._bm25 = BM25Okapi([c.text.lower().split() for c in self._chunks])

    # ---------------- search ----------------
    def _dense(self, query: str, k: int) -> List[Hit]:
        qv = self.embedder.encode(query, normalize_embeddings=True).tolist()
        res = self.qdrant.search(COLLECTION, query_vector=qv, limit=k)
        return [Hit(chunk_id=r.payload["chunk_id"], doc_id=r.payload["doc_id"],
                    text=r.payload["text"], score=r.score, source="dense")
                for r in res]

    def _bm25_search(self, query: str, k: int) -> List[Hit]:
        assert self._bm25 is not None
        scores = self._bm25.get_scores(query.lower().split())
        top = sorted(enumerate(scores), key=lambda x: -x[1])[:k]
        return [Hit(chunk_id=self._chunks[i].chunk_id,
                    doc_id=self._chunks[i].doc_id,
                    text=self._chunks[i].text, score=float(s), source="bm25")
                for i, s in top]

    @staticmethod
    def _rrf(rank_lists: list[list[Hit]], k: int = 60) -> List[Hit]:
        """Reciprocal Rank Fusion."""
        scores: dict[str, Hit] = {}
        accum: dict[str, float] = {}
        for hits in rank_lists:
            for r, h in enumerate(hits):
                accum[h.chunk_id] = accum.get(h.chunk_id, 0) + 1 / (k + r + 1)
                scores[h.chunk_id] = h  # keep last seen Hit (text identical)
        ranked = sorted(accum.items(), key=lambda x: -x[1])
        return [Hit(scores[cid].chunk_id, scores[cid].doc_id, scores[cid].text,
                    score=s, source="rrf") for cid, s in ranked]

    def search(self, query: str, k: int = 5, k_dense: int = 20,
               k_sparse: int = 20, rerank: bool = True) -> List[Hit]:
        dense = self._dense(query, k_dense)
        sparse = self._bm25_search(query, k_sparse)
        fused = self._rrf([dense, sparse])[: max(k * 4, 20)]
        if not rerank:
            return fused[:k]
        pairs = [(query, h.text) for h in fused]
        scores = self.reranker.predict(pairs)
        ranked = sorted(zip(fused, scores), key=lambda x: -x[1])[:k]
        return [Hit(h.chunk_id, h.doc_id, h.text, float(s), "rerank")
                for h, s in ranked]
