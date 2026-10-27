"""
=============================================================================
PROJECT 10: GenAI RAG PLATFORM (CAPSTONE)
=============================================================================
FILE: services/ingestion_service.py
PURPOSE: Orchestrates the document ingestion pipeline

INGESTION PIPELINE:
Document → Chunking → Embedding → Storage

This service coordinates:
1. ChunkingService (splits document)
2. EmbeddingProvider (creates vectors)
3. VectorStore (stores chunks + embeddings)

DEMONSTRATES:
- Dependency Injection (receives interfaces, not implementations)
- Service Layer pattern (orchestration without business rules)
- Composition (combines multiple services)
=============================================================================
"""

from models.document import Document, DocumentChunk
from interfaces.embedding_provider import EmbeddingProvider
from interfaces.vector_store import VectorStore
from services.chunking_service import ChunkingService


class IngestionService:
    """
    Orchestrates the full document ingestion pipeline.

    DEPENDENCY INJECTION IN ACTION:
    - embedding_provider: ANY EmbeddingProvider implementation
    - vector_store: ANY VectorStore implementation
    - chunking_service: Configurable chunking

    This class doesn't know or care about:
    - Which embedding model is used
    - Where vectors are stored
    - How chunking is done

    It just coordinates the FLOW.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        chunking_service: ChunkingService | None = None,
    ):
        """
        Constructor with Dependency Injection.

        ALL dependencies are passed in (not created internally).
        This makes the service:
        - Testable: inject mocks for testing
        - Flexible: swap implementations at runtime
        - Decoupled: no knowledge of concrete classes
        """
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._chunking_service = chunking_service or ChunkingService()

        # Track ingested documents
        self._documents: dict[str, Document] = {}

    def ingest(self, document: Document) -> dict:
        """
        Full ingestion pipeline for a single document.

        PIPELINE STEPS:
        ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ Document │ →  │ Chunking │ →  │Embedding │ →  │ Storage  │
        └──────────┘    └──────────┘    └──────────┘    └──────────┘

        Returns:
            Dict with ingestion statistics
        """
        # Step 1: CHUNK the document
        chunks = self._chunking_service.chunk_document(document)

        if not chunks:
            return {"status": "error", "message": "No content to chunk"}

        # Step 2: EMBED each chunk (convert text → vector)
        texts = [chunk.content for chunk in chunks]
        embeddings = self._embedding_provider.embed_batch(texts)

        # Attach embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding.values

        # Step 3: STORE chunks in vector store
        stored_count = self._vector_store.store_batch(chunks)

        # Step 4: Track the document
        document.chunks = chunks
        self._documents[document.document_id] = document

        # Return ingestion report
        chunk_stats = self._chunking_service.get_stats(chunks)
        return {
            "status": "success",
            "document_id": document.document_id,
            "title": document.title,
            "chunks_created": len(chunks),
            "chunks_stored": stored_count,
            "embedding_model": self._embedding_provider.get_model_name(),
            "embedding_dimensions": self._embedding_provider.get_dimensions(),
            "chunk_stats": chunk_stats,
        }

    def ingest_batch(self, documents: list[Document]) -> list[dict]:
        """Ingest multiple documents."""
        return [self.ingest(doc) for doc in documents]

    def remove_document(self, document_id: str) -> bool:
        """Remove a document and all its chunks from the system."""
        if document_id not in self._documents:
            return False

        # Remove from vector store
        self._vector_store.delete_by_document(document_id)

        # Remove from tracking
        del self._documents[document_id]
        return True

    def get_document(self, document_id: str) -> Document | None:
        """Retrieve a tracked document by ID."""
        return self._documents.get(document_id)

    def list_documents(self) -> list[dict]:
        """List all ingested documents with summary info."""
        return [
            {
                "document_id": doc.document_id,
                "title": doc.title,
                "source": doc.source,
                "chunks": len(doc.chunks),
                "created_at": doc.created_at,
            }
            for doc in self._documents.values()
        ]
