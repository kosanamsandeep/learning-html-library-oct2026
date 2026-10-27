from __future__ import annotations
from agents import ResearchGraphAgent

_agent: ResearchGraphAgent | None = None


def _get_agent() -> ResearchGraphAgent:
    global _agent
    if _agent is None:
        _agent = ResearchGraphAgent()
    return _agent


async def research_topic(topic: str) -> dict:
    agent = _get_agent()
    out = await agent.run(topic)
    return {"agent": agent.name, "topic": topic, **out}
