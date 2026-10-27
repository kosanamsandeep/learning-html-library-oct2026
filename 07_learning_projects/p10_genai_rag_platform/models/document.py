"""
=============================================================================
PROJECT 10: GenAI RAG PLATFORM (CAPSTONE)
=============================================================================
FILE: models/document.py
PURPOSE: Core domain models for the RAG system

THIS PROJECT COMBINES ALL PATTERNS FROM P1-P9:
- P1: Classes & Objects (dataclasses throughout)
- P2: Inheritance (base classes, ABC hierarchies)
- P3: Composition (services compose repositories + strategies)
- P4: DTOs (request/response objects separate from domain)
- P5: Schemas (validation at boundaries)
- P6: Repository Pattern (abstract storage)
- P7: Layered Architecture (API → Service → Repository)
- P8: Interfaces & DI (abstract providers, injectable)
- P9: Factory + Strategy (embedding strategies, retrieval strategies)

RAG = Retrieval-Augmented Generation
- RETRIEVAL: Find relevant documents from a knowledge base
- AUGMENTED: Add retrieved context to the LLM prompt
- GENERATION: LLM generates answer using the context
=============================================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid
import hashlib


@dataclass
class DocumentChunk:
    """
    A CHUNK is a piece of a larger document.

    WHY CHUNK?
    - LLMs have token limits (can't process entire books)
    - Smaller chunks = more precise retrieval
    - Each chunk gets its own embedding vector

    EXAMPLE:
    A 10-page PDF might be split into 50 chunks of ~200 words each.
    Each chunk is independently searchable via its embedding.
    """

    chunk_id: str = field(default_factory=lambda: f"CHK-{uuid.uuid4().hex[:8]}")
    document_id: str = ""  # Which document this chunk belongs to
    content: str = ""  # The actual text content
    embedding: list[float] = field(default_factory=list)  # Vector representation
    chunk_index: int = 0  # Position within the original document
    metadata: dict = field(
        default_factory=dict
    )  # Extra info (page number, section, etc.)
    token_count: int = 0  # Number of tokens in this chunk

    def __post_init__(self):
        """Calculate token count (simplified: ~4 chars per token)."""
        if not self.token_count and self.content:
            self.token_count = len(self.content) // 4


@dataclass
class Document:
    """
    A DOCUMENT represents an ingested knowledge source.

    LIFECYCLE:
    1. User uploads a document (PDF, text, URL, etc.)
    2. System splits it into chunks
    3. Each chunk gets an embedding (vector)
    4. Chunks are stored in vector database
    5. At query time, relevant chunks are retrieved

    This is the fundamental unit of the knowledge base.
    """

    document_id: str = field(default_factory=lambda: f"DOC-{uuid.uuid4().hex[:8]}")
    title: str = ""
    source: str = ""  # URL, file path, or API endpoint
    content: str = ""  # Full raw content
    doc_type: str = "TEXT"  # TEXT, PDF, HTML, MARKDOWN
    chunks: list[DocumentChunk] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    content_hash: str = ""  # For deduplication
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Generate content hash for deduplication."""
        if self.content and not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]


@dataclass
class QueryResult:
    """
    Result of a RAG query - contains the retrieved context and generated answer.

    STRUCTURE:
    - query: What the user asked
    - retrieved_chunks: Relevant document pieces found via similarity search
    - context: The assembled context sent to the LLM
    - answer: The LLM's generated response
    - sources: Citation information
    - confidence: How confident the system is (based on similarity scores)
    """

    query_id: str = field(default_factory=lambda: f"QRY-{uuid.uuid4().hex[:8]}")
    query: str = ""
    retrieved_chunks: list[DocumentChunk] = field(default_factory=list)
    context: str = ""
    answer: str = ""
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0
    latency_ms: float = 0.0
    model_used: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class EmbeddingVector:
    """
    An embedding is a numerical VECTOR that represents the meaning of text.

    KEY INSIGHT:
    - "King" and "Queen" have similar embeddings (both royalty)
    - "King" and "Bicycle" have very different embeddings
    - We use cosine similarity to find "nearest" embeddings

    DIMENSIONS:
    - Simple models: 384 dimensions
    - OpenAI ada-002: 1536 dimensions
    - Each dimension captures some aspect of meaning
    """

    vector_id: str = field(default_factory=lambda: f"VEC-{uuid.uuid4().hex[:8]}")
    values: list[float] = field(default_factory=list)
    source_text: str = ""
    model_name: str = ""
    dimensions: int = 0

    def __post_init__(self):
        """Set dimensions from vector length."""
        if self.values and not self.dimensions:
            self.dimensions = len(self.values)
