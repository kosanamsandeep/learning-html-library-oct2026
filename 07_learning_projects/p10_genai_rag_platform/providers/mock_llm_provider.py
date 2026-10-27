"""
=============================================================================
PROJECT 10: GenAI RAG PLATFORM (CAPSTONE)
=============================================================================
FILE: providers/mock_llm_provider.py
PURPOSE: Simulated LLM provider for testing and demonstration

IN PRODUCTION:
- This would call OpenAI GPT-4, Anthropic Claude, etc.
- Here: simulates LLM behavior with template-based responses
- Architecture remains identical - just swap the provider

DEMONSTRATES:
- Interface implementation (from P8)
- Strategy pattern (from P9) - the LLM is a "generation strategy"
- Dependency Inversion - services depend on LLMProvider, not this class
=============================================================================
"""

import time
from interfaces.llm_provider import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """
    SIMULATED LLM that generates answers based on provided context.

    In a real system:
    - This would make API calls to OpenAI/Anthropic/etc.
    - Handle rate limits, retries, streaming
    - Manage token counting and cost tracking

    For this demo:
    - It extracts key info from the context
    - Generates a structured response
    - Simulates latency and token counting
    """

    def __init__(self, model_name: str = "mock-gpt-4"):
        """Initialize the object with the dependencies or starting values it needs."""
        self._model_name = model_name
        self._max_context = 8192  # Token limit

    def generate(self, prompt: str, max_tokens: int = 500) -> LLMResponse:
        """
        Generate a response from the prompt.

        REAL FLOW:
        1. Receive prompt (system + context + user query)
        2. Count tokens to ensure within limits
        3. Call API
        4. Return structured response

        SIMULATED FLOW:
        1. Extract context and question from prompt
        2. Generate a template-based answer
        3. Simulate realistic metrics
        """
        start_time = time.time()

        # Simulate processing delay (real LLMs take 1-5 seconds)
        # We just measure timing for the logic below

        # Parse the prompt to extract context and question
        context, question = self._parse_prompt(prompt)

        # Generate answer based on available context
        answer = self._generate_answer(context, question)

        # Calculate metrics
        latency_ms = (time.time() - start_time) * 1000
        tokens_used = len(prompt.split()) + len(answer.split())

        return LLMResponse(
            text=answer,
            model=self._model_name,
            tokens_used=min(tokens_used, max_tokens),
            latency_ms=latency_ms,
            finish_reason="stop",
            metadata={"context_length": len(context), "simulated": True},
        )

    def get_model_name(self) -> str:
        """Return the requested item or information if it exists."""
        return self._model_name

    def get_max_context_length(self) -> int:
        """Return the requested item or information if it exists."""
        return self._max_context

    def _parse_prompt(self, prompt: str) -> tuple[str, str]:
        """Extract context and question from a RAG prompt."""
        # Look for context section
        context = ""
        question = ""

        if "Context:" in prompt and "Question:" in prompt:
            parts = prompt.split("Question:")
            context_part = parts[0]
            question = parts[1].strip() if len(parts) > 1 else ""

            if "Context:" in context_part:
                context = context_part.split("Context:")[1].strip()
        else:
            question = prompt

        return context, question

    def _generate_answer(self, context: str, question: str) -> str:
        """
        Generate a simulated answer.

        Strategy:
        - If context available: synthesize from context
        - If no context: acknowledge the gap
        """
        if not context:
            return (
                f"I don't have enough context to answer: '{question}'. "
                "Please provide relevant documents to the knowledge base."
            )

        # Extract key sentences from context (simulate summarization)
        sentences = [s.strip() for s in context.split(".") if len(s.strip()) > 20]

        if sentences:
            # Build a synthesized answer from context
            key_info = ". ".join(sentences[:3])
            return (
                f"Based on the available knowledge base:\n\n"
                f"{key_info}.\n\n"
                f"This information is relevant to your question about: {question[:100]}"
            )
        else:
            return (
                f"The retrieved context contains information related to your query. "
                f"Key points from the knowledge base address: {question[:100]}"
            )
