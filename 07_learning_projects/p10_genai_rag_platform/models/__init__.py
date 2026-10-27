"""
=============================================================================
MODELS PACKAGE - Domain entities for the RAG Platform
=============================================================================
Contains: Document, DocumentChunk, QueryResult, EmbeddingVector
These are pure data structures (no business logic).
=============================================================================
"""

from models.document import Document, DocumentChunk, QueryResult, EmbeddingVector

__all__ = ["Document", "DocumentChunk", "QueryResult", "EmbeddingVector"]
