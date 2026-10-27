from __future__ import annotations
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    async def run(self, prompt: str) -> dict: ...
