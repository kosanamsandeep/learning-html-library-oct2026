"""
=============================================================================
PROJECT 10: GenAI RAG PLATFORM (CAPSTONE)
=============================================================================
FILE: interfaces/embedding_provider.py
PURPOSE: Abstract interface for embedding generation (Dependency Inversion)

DEPENDENCY INVERSION PRINCIPLE (from P8):
- High-level modules should NOT depend on low-level modules
- Both should depend on ABSTRACTIONS

WHY ABSTRACT?
- Today: use a simple local embedding model
- Tomorrow: switch to OpenAI, Cohere, or HuggingFace
- The service layer NEVER changes - it depends on this interface
=============================================================================
"""

from abc import ABC, abstractmethod
from models.document import EmbeddingVector


class EmbeddingProvider(ABC):
    """
    ABSTRACT INTERFACE: Any embedding model must implement this.

    IMPLEMENTATIONS:
    - LocalEmbeddingProvider (simple hash-based, for demo)
    - OpenAIEmbeddingProvider (calls OpenAI API)
    - HuggingFaceEmbeddingProvider (local transformer model)

    The service layer uses THIS interface, not any specific implementation.
    """

    @abstractmethod
    def embed_text(self, text: str) -> EmbeddingVector:
        """
        Convert text into a vector representation.

        Args:
            text: The text to embed (a chunk, a query, etc.)

        Returns:
            EmbeddingVector containing the numerical representation
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[EmbeddingVector]:
        """
        Embed multiple texts at once (more efficient for bulk operations).

        Args:
            texts: List of texts to embed

        Returns:
            List of EmbeddingVectors in the same order
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the name of the embedding model being used."""
        pass

    @abstractmethod
    def get_dimensions(self) -> int:
        """Return the number of dimensions in the embedding output."""
        pass
