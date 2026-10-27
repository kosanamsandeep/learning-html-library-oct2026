"""Abstract base class for all agents."""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """All agents must expose an async `run(prompt)` coroutine."""

    name: str = "base"

    @abstractmethod
    async def run(self, prompt: str) -> str: ...
