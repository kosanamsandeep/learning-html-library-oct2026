"""
=============================================================================
INTERFACES PACKAGE - Abstract contracts for the RAG Platform
=============================================================================
All service interactions go through these abstractions.
No concrete implementations allowed at the service layer.

Interfaces defined:
- EmbeddingProvider: Text → Vector conversion
- LLMProvider: Prompt → Generated text
- VectorStore: Vector storage and similarity search
=============================================================================
"""

from interfaces.embedding_provider import EmbeddingProvider
from interfaces.llm_provider import LLMProvider, LLMResponse
from interfaces.vector_store import VectorStore

__all__ = ["EmbeddingProvider", "LLMProvider", "LLMResponse", "VectorStore"]
