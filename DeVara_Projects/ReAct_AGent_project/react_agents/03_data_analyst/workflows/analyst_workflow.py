from __future__ import annotations
from agents import DataAnalystAgent

_agent: DataAnalystAgent | None = None


def _get_agent() -> DataAnalystAgent:
    global _agent
    if _agent is None:
        _agent = DataAnalystAgent()
    return _agent


async def ask_analyst(question: str, session_id: str = "default") -> dict:
    agent = _get_agent()
    out = await agent.run(question, session_id=session_id)
    return {"agent": agent.name, "session_id": session_id,
            "question": question, "answer": out}
