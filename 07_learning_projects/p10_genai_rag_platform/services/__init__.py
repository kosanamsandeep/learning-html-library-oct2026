"""
=============================================================================
SERVICES PACKAGE - Business logic and orchestration
=============================================================================
Services coordinate between interfaces, providers, and models.
No service knows about concrete implementations - only abstractions.

Services:
- ChunkingService: Splits documents into searchable pieces
- IngestionService: Orchestrates Document → Chunks → Embeddings → Storage
- RetrievalService: Finds relevant chunks for a query
- RAGService: Full RAG pipeline (Retrieve → Augment → Generate)
=============================================================================
"""

from services.chunking_service import ChunkingService
from services.ingestion_service import IngestionService
from services.retrieval_service import RetrievalService
from services.rag_service import RAGService

__all__ = ["ChunkingService", "IngestionService", "RetrievalService", "RAGService"]
