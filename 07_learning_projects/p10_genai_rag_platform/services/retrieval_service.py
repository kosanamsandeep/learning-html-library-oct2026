"""
=============================================================================
PROJECT 10: GenAI RAG PLATFORM (CAPSTONE)
=============================================================================
FILE: services/retrieval_service.py
PURPOSE: Handles the RETRIEVAL part of RAG

RETRIEVAL = Finding relevant information from the knowledge base.

FLOW:
1. User asks a question
2. Question is EMBEDDED (converted to vector)
3. Vector store finds similar chunks (similarity search)
4. Top-K most relevant chunks are returned as context

THIS IS THE "R" IN RAG:
- Without retrieval: LLM hallucinates (makes things up)
- With retrieval: LLM answers grounded in actual documents
=============================================================================
"""

from interfaces.embedding_provider import EmbeddingProvider
from interfaces.vector_store import VectorStore
from models.document import DocumentChunk


class RetrievalService:
    """
    Service responsible for finding relevant document chunks.

    ARCHITECTURE:
    - Depends on EmbeddingProvider (to embed the query)
    - Depends on VectorStore (to search for similar chunks)
    - Returns ranked chunks with similarity scores

    TUNING PARAMETERS:
    - top_k: How many chunks to retrieve (more = more context, slower)
    - threshold: Minimum similarity score to include (filters noise)
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        default_top_k: int = 5,
        similarity_threshold: float = 0.1,
    ):
        """
        Initialize with injected dependencies.

        Args:
            embedding_provider: Converts query text to vector
            vector_store: Searches for similar vectors
            default_top_k: Default number of results to return
            similarity_threshold: Minimum similarity to include in results
        """
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._default_top_k = default_top_k
        self._similarity_threshold = similarity_threshold

    def retrieve(
        self, query: str, top_k: int | None = None
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Retrieve relevant chunks for a query.

        STEPS:
        1. Embed the query (same model as documents!)
        2. Search vector store for similar embeddings
        3. Filter by threshold
        4. Return (chunk, score) pairs

        WHY SAME EMBEDDING MODEL?
        Query and documents MUST use the same embedding model.
        Otherwise, vectors live in different "spaces" and
        similarity comparison is meaningless.
        """
        k = top_k or self._default_top_k

        # Step 1: Embed the query
        query_embedding = self._embedding_provider.embed_text(query)

        # Step 2: Search vector store
        results = self._vector_store.search(query_embedding.values, top_k=k)

        # Step 3: Filter by similarity threshold
        filtered = [
            (chunk, score)
            for chunk, score in results
            if score >= self._similarity_threshold
        ]

        return filtered

    def retrieve_with_context(self, query: str, top_k: int | None = None) -> str:
        """
        Retrieve and format chunks as a context string for the LLM.

        This is what gets inserted into the LLM prompt as "context".
        """
        results = self.retrieve(query, top_k)

        if not results:
            return "No relevant information found in the knowledge base."

        # Format chunks into a readable context
        context_parts = []
        for i, (chunk, score) in enumerate(results, 1):
            source = chunk.metadata.get("doc_title", "Unknown")
            context_parts.append(
                f"[Source {i}: {source} | Relevance: {score:.2f}]\n{chunk.content}"
            )

        return "\n\n---\n\n".join(context_parts)

    def get_sources(self, query: str, top_k: int | None = None) -> list[dict]:
        """Return source metadata for retrieved chunks."""
        results = self.retrieve(query, top_k)

        return [
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "source": chunk.metadata.get("source", ""),
                "title": chunk.metadata.get("doc_title", ""),
                "relevance_score": round(score, 4),
                "preview": chunk.content[:100] + "...",
            }
            for chunk, score in results
        ]
