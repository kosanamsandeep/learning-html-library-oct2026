from __future__ import annotations
from agents import LGCalcWikiAgent

_agent: LGCalcWikiAgent | None = None


def _get_agent() -> LGCalcWikiAgent:
    global _agent
    if _agent is None:
        _agent = LGCalcWikiAgent()
    return _agent


async def answer_question(question: str, thread_id: str = "default") -> dict:
    agent = _get_agent()
    output = await agent.run(question, thread_id=thread_id)
    return {"agent": agent.name, "thread_id": thread_id,
            "question": question, "answer": output}
