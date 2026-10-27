"""
=============================================================================
PROJECT 10: GenAI RAG PLATFORM (CAPSTONE)
=============================================================================
FILE: interfaces/llm_provider.py
PURPOSE: Abstract interface for LLM (Large Language Model) generation

THIS IS THE "GENERATION" PART OF RAG:
- After retrieving relevant context...
- We pass the context + user query to an LLM
- The LLM generates a grounded answer

IMPLEMENTATIONS COULD BE:
- OpenAI GPT-4
- Anthropic Claude
- Google Gemini
- Local Llama/Mistral
- Mock provider (for testing)
=============================================================================
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    """Response from an LLM generation call."""

    text: str = ""
    model: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0
    finish_reason: str = ""  # "stop", "length", "error"
    metadata: dict = field(default_factory=dict)


class LLMProvider(ABC):
    """
    ABSTRACT INTERFACE: Any LLM must implement this.

    USAGE IN RAG:
    1. System builds a prompt with context + query
    2. Calls llm_provider.generate(prompt)
    3. Returns the generated answer

    The RAG service doesn't care if it's GPT-4, Claude, or a local model.
    It just needs something that takes text in and produces text out.
    """

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 500) -> LLMResponse:
        """
        Generate text from a prompt.

        Args:
            prompt: The full prompt (includes system message + context + query)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with the generated text
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier."""
        pass

    @abstractmethod
    def get_max_context_length(self) -> int:
        """Return max tokens the model can handle as input."""
        pass
