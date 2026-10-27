"""High-level workflow that wires the agent to a request/response shape."""
from __future__ import annotations

from agents import ReactCalcWikiAgent

_agent: ReactCalcWikiAgent | None = None


def _get_agent() -> ReactCalcWikiAgent:
    global _agent
    if _agent is None:
        _agent = ReactCalcWikiAgent()
    return _agent


async def answer_question(question: str) -> dict:
    agent = _get_agent()
    output = await agent.run(question)
    return {"agent": agent.name, "question": question, "answer": output}
