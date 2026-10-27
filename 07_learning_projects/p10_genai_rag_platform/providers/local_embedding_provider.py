"""
=============================================================================
PROJECT 10: GenAI RAG PLATFORM (CAPSTONE)
=============================================================================
FILE: providers/local_embedding_provider.py
PURPOSE: Concrete implementation of EmbeddingProvider (DI-injectable)

THIS IS A SIMULATED EMBEDDING MODEL:
- In production: calls OpenAI, Cohere, or runs a local transformer
- Here: uses a deterministic hash-based approach for demonstration
- The architecture is identical — only the embed logic differs

KEY POINT: The service layer uses EmbeddingProvider (abstract).
This class can be swapped for any real model without changing services.
=============================================================================
"""

import hashlib
import math
from interfaces.embedding_provider import EmbeddingProvider
from models.document import EmbeddingVector


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    SIMULATED embedding provider using hash-based vectors.

    HOW IT WORKS (simplified for learning):
    1. Takes text input
    2. Generates a deterministic vector using character-level hashing
    3. Normalizes the vector (unit length for cosine similarity)

    WHY DETERMINISTIC?
    - Same text always produces same embedding
    - Similar texts produce somewhat similar embeddings
    - Enables reproducible testing

    IN PRODUCTION, replace with:
        class OpenAIEmbeddingProvider(EmbeddingProvider):
            def embed_text(self, text):
                response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
                return EmbeddingVector(values=response['data'][0]['embedding'], ...)
    """

    def __init__(self, dimensions: int = 128):
        """
        Initialize with configurable dimensions.

        Real models have fixed dimensions:
        - all-MiniLM-L6-v2: 384
        - text-embedding-ada-002: 1536
        - text-embedding-3-large: 3072
        """
        self._dimensions = dimensions
        self._model_name = f"local-hash-{dimensions}d"

    def embed_text(self, text: str) -> EmbeddingVector:
        """
        Generate embedding for a single text.

        Algorithm (simplified):
        1. Create overlapping n-grams from the text
        2. Hash each n-gram to get a position + value
        3. Accumulate into a vector
        4. Normalize to unit length
        """
        values = self._generate_embedding(text)
        return EmbeddingVector(
            values=values,
            source_text=text[:100],  # Store first 100 chars for reference
            model_name=self._model_name,
            dimensions=self._dimensions,
        )

    def embed_batch(self, texts: list[str]) -> list[EmbeddingVector]:
        """Embed multiple texts. In production, this would be a single API call."""
        return [self.embed_text(text) for text in texts]

    def get_model_name(self) -> str:
        """Return the requested item or information if it exists."""
        return self._model_name

    def get_dimensions(self) -> int:
        """Return the requested item or information if it exists."""
        return self._dimensions

    def _generate_embedding(self, text: str) -> list[float]:
        """
        Generate a deterministic embedding vector from text.

        This simplistic approach:
        1. Creates character trigrams
        2. Hashes each trigram
        3. Maps hash to vector positions
        4. Normalizes to unit vector

        Similar texts will have somewhat similar vectors because
        they share many of the same trigrams.
        """
        # Initialize zero vector
        vector = [0.0] * self._dimensions

        # Process text: lowercase, create trigrams
        text_lower = text.lower().strip()
        if not text_lower:
            return vector

        # Generate trigrams and accumulate into vector
        for i in range(len(text_lower) - 2):
            trigram = text_lower[i : i + 3]
            # Hash the trigram
            h = hashlib.md5(trigram.encode()).hexdigest()
            # Map to position and value
            position = int(h[:8], 16) % self._dimensions
            value = (int(h[8:16], 16) % 1000) / 1000.0 - 0.5
            vector[position] += value

        # Normalize to unit vector (required for cosine similarity)
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]

        return vector
