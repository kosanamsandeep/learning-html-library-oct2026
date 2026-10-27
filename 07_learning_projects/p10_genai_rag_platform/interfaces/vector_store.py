"""
=============================================================================
PROJECT 10: GenAI RAG PLATFORM (CAPSTONE)
=============================================================================
FILE: interfaces/vector_store.py
PURPOSE: Abstract interface for vector storage (Repository Pattern from P6)

VECTOR STORE = The "database" for embeddings.
Unlike a regular DB that matches exact values,
a vector store finds "similar" items using distance metrics.

REAL IMPLEMENTATIONS:
- Pinecone, Weaviate, Qdrant, ChromaDB, FAISS, pgvector

WE USE: Abstract interface so we can swap implementations freely.
=============================================================================
"""

from abc import ABC, abstractmethod
from models.document import DocumentChunk


class VectorStore(ABC):
    """
    ABSTRACT INTERFACE: Vector database operations.

    This is a REPOSITORY PATTERN (from P6) applied to vector storage.
    The service layer doesn't know if vectors are stored in:
    - Memory (for testing)
    - FAISS (for local)
    - Pinecone (for production)
    - PostgreSQL pgvector (for hybrid)
    """

    @abstractmethod
    def store(self, chunk: DocumentChunk) -> bool:
        """Store a chunk with its embedding vector."""
        pass

    @abstractmethod
    def store_batch(self, chunks: list[DocumentChunk]) -> int:
        """Store multiple chunks. Returns count of successful stores."""
        pass

    @abstractmethod
    def search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Find the top_k most similar chunks to the query embedding.

        Returns: List of (chunk, similarity_score) tuples, sorted by relevance.
        Similarity score is typically cosine similarity (0.0 to 1.0).
        """
        pass

    @abstractmethod
    def delete(self, chunk_id: str) -> bool:
        """Delete a chunk by ID."""
        pass

    @abstractmethod
    def delete_by_document(self, document_id: str) -> int:
        """Delete all chunks belonging to a document. Returns count deleted."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total number of stored chunks."""
        pass
