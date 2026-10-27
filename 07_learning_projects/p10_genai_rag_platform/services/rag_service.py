"""
=============================================================================
PROJECT 10: GenAI RAG PLATFORM (CAPSTONE)
=============================================================================
FILE: services/rag_service.py
PURPOSE: The MAIN RAG orchestrator - brings everything together

THIS IS THE HEART OF THE SYSTEM:
It coordinates the full RAG pipeline:
    Query → Retrieve → Augment → Generate → Return

ARCHITECTURE (Layered + DI + Composition):
┌─────────────────────────────────────────────────┐
│               RAG Service                        │
│  (Orchestrates the full pipeline)               │
├─────────────────────────────────────────────────┤
│  RetrievalService    │    LLMProvider           │
│  (finds context)     │    (generates answers)   │
├──────────────────────┼──────────────────────────┤
│  EmbeddingProvider   │    VectorStore           │
│  (creates vectors)   │    (stores/searches)     │
└─────────────────────────────────────────────────┘
=============================================================================
"""

import time
from interfaces.llm_provider import LLMProvider
from services.retrieval_service import RetrievalService
from models.document import QueryResult


class RAGService:
    """
    The main RAG (Retrieval-Augmented Generation) service.

    WHAT IT DOES:
    1. Takes a user question
    2. RETRIEVES relevant context from the knowledge base
    3. AUGMENTS an LLM prompt with that context
    4. GENERATES an answer grounded in the retrieved info

    WHY RAG?
    - LLMs alone hallucinate (make things up)
    - LLMs don't know your private data
    - RAG grounds answers in YOUR documents
    - RAG provides citations (which documents were used)

    PATTERN USAGE:
    - Composition: Composes RetrievalService + LLMProvider
    - DI: Both dependencies are injected via constructor
    - Strategy: LLMProvider is a strategy (swap GPT-4 for Claude)
    - Layered: Service layer orchestrates without knowing details
    """

    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_provider: LLMProvider,
    ):
        """
        Initialize with injected dependencies.

        DEPENDENCY INJECTION:
        - retrieval_service: Handles finding relevant chunks
        - llm_provider: Generates the final answer

        Neither is created here — both injected from outside.
        This makes testing trivial (inject mocks).
        """
        self._retrieval = retrieval_service
        self._llm = llm_provider
        self._query_history: list[QueryResult] = []

    def query(self, question: str, top_k: int = 5) -> QueryResult:
        """
        Execute a full RAG query.

        THE FULL RAG PIPELINE:
        ┌────────────┐
        │  Question   │  "What is dependency injection?"
        └─────┬──────┘
              │
        ┌─────▼──────┐
        │  RETRIEVE   │  Find relevant chunks from vector store
        └─────┬──────┘
              │
        ┌─────▼──────┐
        │  AUGMENT    │  Build prompt with context + question
        └─────┬──────┘
              │
        ┌─────▼──────┐
        │  GENERATE   │  LLM produces answer from prompt
        └─────┬──────┘
              │
        ┌─────▼──────┐
        │  RETURN     │  Answer + sources + confidence
        └────────────┘
        """
        start_time = time.time()

        # STEP 1: RETRIEVE relevant context
        retrieved = self._retrieval.retrieve(question, top_k=top_k)
        context = self._retrieval.retrieve_with_context(question, top_k=top_k)

        # STEP 2: AUGMENT - Build the LLM prompt with context
        prompt = self._build_prompt(question, context)

        # STEP 3: GENERATE - Call the LLM
        llm_response = self._llm.generate(prompt)

        # STEP 4: Build the result
        sources = [
            f"{chunk.metadata.get('doc_title', 'Unknown')} (score: {score:.2f})"
            for chunk, score in retrieved
        ]

        # Calculate confidence (average similarity of top results)
        confidence = 0.0
        if retrieved:
            confidence = sum(score for _, score in retrieved) / len(retrieved)

        latency_ms = (time.time() - start_time) * 1000

        result = QueryResult(
            query=question,
            retrieved_chunks=[chunk for chunk, _ in retrieved],
            context=context,
            answer=llm_response.text,
            sources=sources,
            confidence=confidence,
            latency_ms=latency_ms,
            model_used=self._llm.get_model_name(),
        )

        # Track in history
        self._query_history.append(result)

        return result

    def _build_prompt(self, question: str, context: str) -> str:
        """
        Build the augmented prompt for the LLM.

        PROMPT ENGINEERING:
        The prompt structure matters enormously for answer quality.

        STRUCTURE:
        1. System instruction (who the LLM is, how to behave)
        2. Context (retrieved documents)
        3. Question (what the user wants to know)
        4. Format instruction (how to structure the answer)
        """
        return f"""You are a helpful AI assistant. Answer the question based ONLY on the provided context. 
If the context doesn't contain enough information, say so honestly.

Context:
{context}

Question: {question}

Instructions:
- Answer based on the context provided above
- If unsure, say "I don't have enough information"
- Cite which sources you used
- Be concise but thorough"""

    def get_query_history(self) -> list[dict]:
        """Return query history with key metrics."""
        return [
            {
                "query_id": qr.query_id,
                "query": qr.query,
                "answer_preview": qr.answer[:100] + "...",
                "confidence": round(qr.confidence, 3),
                "sources_count": len(qr.sources),
                "latency_ms": round(qr.latency_ms, 2),
                "model": qr.model_used,
                "timestamp": qr.timestamp,
            }
            for qr in self._query_history
        ]

    def get_stats(self) -> dict:
        """Return overall RAG system statistics."""
        if not self._query_history:
            return {"total_queries": 0}

        confidences = [qr.confidence for qr in self._query_history]
        latencies = [qr.latency_ms for qr in self._query_history]

        return {
            "total_queries": len(self._query_history),
            "avg_confidence": round(sum(confidences) / len(confidences), 3),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
            "model": self._llm.get_model_name(),
        }
