from __future__ import annotations
from agents import ResearchAgent

_agent: ResearchAgent | None = None


def _get_agent() -> ResearchAgent:
    global _agent
    if _agent is None:
        _agent = ResearchAgent()
    return _agent


async def research_topic(topic: str) -> dict:
    agent = _get_agent()
    out = await agent.run(topic)
    return {"agent": agent.name, "topic": topic, "result": out}
