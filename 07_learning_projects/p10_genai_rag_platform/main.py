"""
=============================================================================
PROJECT 10: GenAI RAG PLATFORM (CAPSTONE)
=============================================================================
FILE: main.py
PURPOSE: Full demonstration of the RAG Platform

THIS DEMO SHOWS:
1. System initialization with DI (Dependency Injection)
2. Document ingestion pipeline (Chunk → Embed → Store)
3. RAG queries (Retrieve → Augment → Generate)
4. Adding new documents and re-querying
5. System analytics

RUN:
    cd projects/p10_genai_rag_platform
    python main.py
=============================================================================
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.document import Document
from providers.local_embedding_provider import LocalEmbeddingProvider
from providers.mock_llm_provider import MockLLMProvider
from providers.memory_vector_store import MemoryVectorStore
from services.chunking_service import ChunkingService
from services.ingestion_service import IngestionService
from services.retrieval_service import RetrievalService
from services.rag_service import RAGService


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subheader(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n  --- {title} ---")


def create_sample_documents() -> list[Document]:
    """
    Create sample documents for the knowledge base.

    In production, these would come from:
    - PDF uploads
    - Web scraping
    - API feeds
    - Database exports
    """
    docs = [
        Document(
            title="Python Design Patterns",
            source="internal-wiki/design-patterns",
            doc_type="TEXT",
            content="""Design Patterns in Python

The Factory Pattern is a creational design pattern that provides an interface for creating objects without specifying their exact class. In Python, factory methods are often implemented as class methods that return instances of different subclasses based on input parameters.

The Strategy Pattern is a behavioral design pattern that enables selecting algorithms at runtime. Instead of implementing a single algorithm directly, code receives runtime instructions about which family of algorithms to use. In Python, strategies can be implemented as classes with a common interface or even as simple functions passed as parameters.

The Repository Pattern provides an abstraction layer between your domain logic and data access code. It centralizes common data access functionality, providing better maintainability and decoupling the infrastructure from the domain layer. Think of it as a collection of domain objects in memory.

Dependency Injection is a technique where an object receives its dependencies from external sources rather than creating them internally. In Python, this is typically done through constructor parameters. DI makes code more testable, flexible, and follows the Dependency Inversion Principle - depend on abstractions, not concretions.""",
        ),
        Document(
            title="RAG Architecture Guide",
            source="docs/rag-architecture",
            doc_type="TEXT",
            content="""Retrieval-Augmented Generation (RAG) Architecture

RAG is a technique that enhances Large Language Model responses by providing relevant context from a knowledge base. The core idea is simple: instead of relying solely on the LLM's training data, we first RETRIEVE relevant documents, then AUGMENT the prompt with this context, and finally let the LLM GENERATE an answer grounded in real data.

The RAG pipeline consists of two main phases. The Ingestion Phase processes documents by splitting them into chunks, generating embedding vectors for each chunk, and storing them in a vector database. The Query Phase takes a user question, embeds it using the same model, finds similar chunks via vector similarity search, and passes the retrieved context to an LLM for answer generation.

Key components of a RAG system include the Embedding Model which converts text to numerical vectors, the Vector Store which enables fast similarity search, the Chunking Strategy which determines how documents are split, and the LLM which generates the final answer. Each component can be swapped independently thanks to clean interfaces.

Common challenges in RAG include chunk size optimization, embedding model selection, handling multi-document queries, managing context window limits, and ensuring answer faithfulness to the source material.""",
        ),
        Document(
            title="SOLID Principles Guide",
            source="docs/solid-principles",
            doc_type="TEXT",
            content="""SOLID Principles in Software Engineering

The Single Responsibility Principle states that a class should have only one reason to change. Each class or module should focus on doing one thing well. In a RAG system, this means the ChunkingService only handles splitting, the EmbeddingProvider only handles vectorization, and the VectorStore only handles storage and search.

The Open/Closed Principle means software entities should be open for extension but closed for modification. You should be able to add new functionality without changing existing code. For example, adding a new embedding model should not require modifying the RAG service. This is achieved through abstract interfaces.

The Liskov Substitution Principle states that objects of a superclass should be replaceable with objects of its subclasses without breaking the application. Any EmbeddingProvider implementation should work wherever EmbeddingProvider is expected.

The Interface Segregation Principle suggests that no client should be forced to depend on interfaces it does not use. Keep interfaces focused and specific rather than creating one large interface.

The Dependency Inversion Principle states that high-level modules should not depend on low-level modules - both should depend on abstractions. The RAGService depends on EmbeddingProvider and VectorStore interfaces, not on specific implementations like OpenAI or Pinecone.""",
        ),
    ]
    return docs


def demo_system_initialization():
    """
    DEMO 1: Initialize the RAG system using Dependency Injection.

    This shows how all components are wired together.
    In production, a DI container (like dependency-injector) would do this.
    """
    print_header("DEMO 1: System Initialization (Dependency Injection)")

    # STEP 1: Create concrete implementations
    print("\n  Creating concrete providers:")
    embedding_provider = LocalEmbeddingProvider(dimensions=128)
    print(f"    ✅ EmbeddingProvider: {embedding_provider.get_model_name()}")
    print(f"       Dimensions: {embedding_provider.get_dimensions()}")

    llm_provider = MockLLMProvider(model_name="mock-gpt-4-turbo")
    print(f"    ✅ LLMProvider: {llm_provider.get_model_name()}")
    print(f"       Max context: {llm_provider.get_max_context_length()} tokens")

    vector_store = MemoryVectorStore()
    print(f"    ✅ VectorStore: MemoryVectorStore (in-memory)")

    chunking_service = ChunkingService(chunk_size=400, overlap=50)
    print(f"    ✅ ChunkingService: chunk_size=400, overlap=50")

    # STEP 2: Wire up services via DI (constructor injection)
    print("\n  Wiring services via Dependency Injection:")

    ingestion_service = IngestionService(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        chunking_service=chunking_service,
    )
    print(
        "    ✅ IngestionService (embedding_provider, vector_store, chunking_service)"
    )

    retrieval_service = RetrievalService(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        default_top_k=3,
        similarity_threshold=0.05,
    )
    print("    ✅ RetrievalService (embedding_provider, vector_store)")

    rag_service = RAGService(
        retrieval_service=retrieval_service,
        llm_provider=llm_provider,
    )
    print("    ✅ RAGService (retrieval_service, llm_provider)")

    print("\n  🎯 KEY INSIGHT: No service creates its own dependencies!")
    print("     Everything is injected → testable, swappable, decoupled.")

    return ingestion_service, retrieval_service, rag_service, vector_store


def demo_document_ingestion(ingestion_service: IngestionService):
    """
    DEMO 2: Ingest documents into the knowledge base.
    """
    print_header("DEMO 2: Document Ingestion Pipeline")

    documents = create_sample_documents()

    print(f"\n  Ingesting {len(documents)} documents...")
    print("  Pipeline: Document → Chunk → Embed → Store\n")

    for doc in documents:
        result = ingestion_service.ingest(doc)
        print(f"  📄 '{result['title']}'")
        print(
            f"     Chunks: {result['chunks_created']} | Stored: {result['chunks_stored']}"
        )
        print(
            f"     Embedding: {result['embedding_model']} ({result['embedding_dimensions']}D)"
        )
        stats = result["chunk_stats"]
        print(
            f"     Chunk sizes: avg={stats['avg_size']}, min={stats['min_size']}, max={stats['max_size']}"
        )
        print()

    # Show all documents
    print_subheader("Knowledge Base Contents")
    for doc_info in ingestion_service.list_documents():
        print(
            f"    • {doc_info['title']} ({doc_info['chunks']} chunks) - {doc_info['source']}"
        )


def demo_rag_queries(rag_service: RAGService):
    """
    DEMO 3: Execute RAG queries - the full pipeline in action.
    """
    print_header("DEMO 3: RAG Queries (Retrieve → Augment → Generate)")

    questions = [
        "What is the Factory Pattern in Python?",
        "How does RAG work?",
        "Explain dependency injection and why it matters",
        "What are the SOLID principles?",
    ]

    for question in questions:
        print(f"\n  ❓ Question: {question}")
        print("  " + "-" * 60)

        result = rag_service.query(question, top_k=3)

        print(f"  💡 Answer: {result.answer[:200]}...")
        print(f"\n  📊 Metrics:")
        print(f"     Confidence: {result.confidence:.3f}")
        print(f"     Latency: {result.latency_ms:.2f}ms")
        print(f"     Sources used: {len(result.sources)}")
        for source in result.sources[:3]:
            print(f"       - {source}")
        print()


def demo_retrieval_details(retrieval_service: RetrievalService):
    """
    DEMO 4: Show retrieval details - what happens behind the scenes.
    """
    print_header("DEMO 4: Retrieval Deep Dive")

    query = "How do I implement the Strategy Pattern?"
    print(f"\n  Query: '{query}'")
    print(f"\n  Step 1: Query → Embed → Search → Rank")

    sources = retrieval_service.get_sources(query, top_k=5)

    print(f"\n  Step 2: Found {len(sources)} relevant chunks:")
    for i, source in enumerate(sources, 1):
        print(f"\n  [{i}] Score: {source['relevance_score']:.4f}")
        print(f"      Source: {source['title']}")
        print(f"      Preview: {source['preview']}")


def demo_analytics(rag_service: RAGService, vector_store):
    """
    DEMO 5: System analytics and monitoring.
    """
    print_header("DEMO 5: System Analytics")

    stats = rag_service.get_stats()
    print(f"\n  RAG System Stats:")
    print(f"    Total queries: {stats['total_queries']}")
    if stats["total_queries"] > 0:
        print(f"    Avg confidence: {stats['avg_confidence']}")
        print(f"    Avg latency: {stats['avg_latency_ms']}ms")
        print(f"    Model: {stats['model']}")

    print(f"\n  Vector Store Stats:")
    print(f"    Total chunks stored: {vector_store.count()}")

    print(f"\n  Query History:")
    for entry in rag_service.get_query_history():
        print(f"    • [{entry['timestamp'][:19]}] '{entry['query'][:40]}...'")
        print(
            f"      Confidence: {entry['confidence']} | Sources: {entry['sources_count']}"
        )


def main():
    """Run the full RAG platform demonstration."""
    print("\n" + "█" * 70)
    print("█  PROJECT 10: GenAI RAG PLATFORM (CAPSTONE)                       █")
    print("█  Combines ALL patterns: OOP, Inheritance, Composition, DTOs,     █")
    print("█  Repository, Layered Arch, Interfaces/DI, Strategy/Factory       █")
    print("█" * 70)

    # Initialize system
    ingestion_service, retrieval_service, rag_service, vector_store = (
        demo_system_initialization()
    )

    # Ingest documents
    demo_document_ingestion(ingestion_service)

    # Run RAG queries
    demo_rag_queries(rag_service)

    # Show retrieval details
    demo_retrieval_details(retrieval_service)

    # Show analytics
    demo_analytics(rag_service, vector_store)

    # Final learning summary
    print_header("CAPSTONE LEARNING SUMMARY")
    print("""
  🎓 PATTERNS COMBINED IN THIS PROJECT:

  ┌─────────────────────────────────────────────────────────────────┐
  │  Pattern              │ Where Used                              │
  ├─────────────────────────────────────────────────────────────────┤
  │  Classes & Objects    │ Document, DocumentChunk, QueryResult    │
  │  Inheritance          │ All providers inherit from ABC          │
  │  Composition          │ RAGService composes Retrieval + LLM     │
  │  DTOs/Dataclasses     │ All models are pure data containers     │
  │  Repository Pattern   │ VectorStore (abstract storage)          │
  │  Layered Architecture │ API → Service → Provider layers         │
  │  Interfaces & DI      │ EmbeddingProvider, LLMProvider, VectorStore │
  │  Strategy Pattern     │ Swappable embedding models, LLMs        │
  │  Factory Pattern      │ Document/Chunk creation in services     │
  │  SOLID Principles     │ Throughout the entire codebase          │
  └─────────────────────────────────────────────────────────────────┘

  🏗️ ARCHITECTURE SUMMARY:

  User Query → RAGService → RetrievalService → EmbeddingProvider (embed query)
                                             → VectorStore (similarity search)
                          → LLMProvider (generate answer with context)
                          → QueryResult (answer + sources + confidence)

  Document  → IngestionService → ChunkingService (split)
                               → EmbeddingProvider (embed chunks)
                               → VectorStore (store)

  🔑 KEY TAKEAWAY:
  Every component is:
  - INDEPENDENT (can be tested alone)
  - SWAPPABLE (change implementation without changing clients)
  - FOCUSED (single responsibility)
  - ABSTRACT (depends on interfaces, not implementations)

  This is production-grade architecture used at companies like
  OpenAI, Anthropic, Google, and every serious RAG platform.
    """)


if __name__ == "__main__":
    main()
