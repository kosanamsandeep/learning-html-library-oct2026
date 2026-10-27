"""
=============================================================================
PROVIDERS PACKAGE - Concrete implementations of interfaces
=============================================================================
These are the "pluggable" components:
- LocalEmbeddingProvider → implements EmbeddingProvider
- MockLLMProvider → implements LLMProvider
- MemoryVectorStore → implements VectorStore

Swap any of these for production implementations WITHOUT changing services.
=============================================================================
"""

from providers.local_embedding_provider import LocalEmbeddingProvider
from providers.mock_llm_provider import MockLLMProvider
from providers.memory_vector_store import MemoryVectorStore

__all__ = ["LocalEmbeddingProvider", "MockLLMProvider", "MemoryVectorStore"]
