from __future__ import annotations
from agents import DataAnalystSupervisor

_agent: DataAnalystSupervisor | None = None


def _get_agent() -> DataAnalystSupervisor:
    global _agent
    if _agent is None:
        _agent = DataAnalystSupervisor()
    return _agent


async def ask_analyst(question: str, thread_id: str = "default") -> dict:
    agent = _get_agent()
    out = await agent.run(question, thread_id=thread_id)
    return {"agent": agent.name, "thread_id": thread_id,
            "question": question, "answer": out}
