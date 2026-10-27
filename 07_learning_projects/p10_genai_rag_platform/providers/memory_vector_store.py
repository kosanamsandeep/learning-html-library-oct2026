"""
=============================================================================
PROJECT 10: GenAI RAG PLATFORM (CAPSTONE)
=============================================================================
FILE: providers/memory_vector_store.py
PURPOSE: In-memory vector store implementation (Repository Pattern)

THIS IS THE VECTOR "DATABASE":
- Stores document chunks with their embedding vectors
- Performs similarity search using cosine similarity
- In-memory for demo; in production: Pinecone, ChromaDB, pgvector

COSINE SIMILARITY EXPLAINED:
- Measures angle between two vectors (not distance)
- Range: -1 to 1 (1 = identical, 0 = unrelated, -1 = opposite)
- Used universally in embeddings because it ignores magnitude
=============================================================================
"""

import math
from interfaces.vector_store import VectorStore
from models.document import DocumentChunk


class MemoryVectorStore(VectorStore):
    """
    IN-MEMORY vector store using brute-force cosine similarity search.

    TRADE-OFFS:
    - ✅ Simple, no dependencies, great for testing
    - ✅ Exact results (no approximation)
    - ❌ O(n) search - doesn't scale beyond ~100k chunks
    - ❌ Not persistent - data lost on restart

    IN PRODUCTION:
    - Use FAISS for local (approximate nearest neighbor, very fast)
    - Use Pinecone/Qdrant for cloud (managed, scalable)
    - Use pgvector for PostgreSQL integration

    ALL implementations share the same VectorStore interface!
    """

    def __init__(self):
        # Storage: dict of chunk_id → DocumentChunk
        """Initialize the object with the dependencies or starting values it needs."""
        self._store: dict[str, DocumentChunk] = {}

    def store(self, chunk: DocumentChunk) -> bool:
        """Store a single chunk with its embedding."""
        if not chunk.embedding:
            return False  # Can't store without embedding
        self._store[chunk.chunk_id] = chunk
        return True

    def store_batch(self, chunks: list[DocumentChunk]) -> int:
        """Store multiple chunks. Returns count of successful stores."""
        count = 0
        for chunk in chunks:
            if self.store(chunk):
                count += 1
        return count

    def search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[tuple[DocumentChunk, float]]:
        """
        SIMILARITY SEARCH: Find the most similar chunks to the query.

        Algorithm:
        1. Compute cosine similarity between query and EVERY stored chunk
        2. Sort by similarity (highest first)
        3. Return top_k results

        COSINE SIMILARITY FORMULA:
            cos(A, B) = (A · B) / (|A| × |B|)

        Where:
            A · B = sum of element-wise products
            |A| = magnitude (sqrt of sum of squares)
        """
        if not query_embedding or not self._store:
            return []

        # Calculate similarity with every stored chunk
        results: list[tuple[DocumentChunk, float]] = []

        for chunk in self._store.values():
            if chunk.embedding:
                similarity = self._cosine_similarity(query_embedding, chunk.embedding)
                results.append((chunk, similarity))

        # Sort by similarity (descending) and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def delete(self, chunk_id: str) -> bool:
        """Delete a chunk by ID."""
        if chunk_id in self._store:
            del self._store[chunk_id]
            return True
        return False

    def delete_by_document(self, document_id: str) -> int:
        """Delete all chunks belonging to a document."""
        to_delete = [
            cid
            for cid, chunk in self._store.items()
            if chunk.document_id == document_id
        ]
        for cid in to_delete:
            del self._store[cid]
        return len(to_delete)

    def count(self) -> int:
        """Return total number of stored chunks."""
        return len(self._store)

    @staticmethod
    def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        MATH:
            cos(θ) = (A · B) / (||A|| × ||B||)

        INTERPRETATION:
            1.0  = vectors point in same direction (identical meaning)
            0.0  = vectors are perpendicular (unrelated)
            -1.0 = vectors point opposite (opposite meaning)

        STEPS:
        1. Dot product: sum of element-wise multiplication
        2. Magnitudes: sqrt of sum of squares for each vector
        3. Divide dot product by product of magnitudes
        """
        if len(vec_a) != len(vec_b):
            return 0.0

        # Step 1: Dot product (A · B)
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))

        # Step 2: Magnitudes (||A|| and ||B||)
        magnitude_a = math.sqrt(sum(a * a for a in vec_a))
        magnitude_b = math.sqrt(sum(b * b for b in vec_b))

        # Step 3: Cosine similarity
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)
