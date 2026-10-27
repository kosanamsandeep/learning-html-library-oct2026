"""Self-critique skill — LLM grades the draft answer."""
from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage
from models.model_client import get_chat_model

_SYS = (
    "You are a strict reviewer. Given a draft analyst answer, respond in 2 lines: "
    "'OK' if it directly answers and is supported by data, otherwise list what's missing."
)


async def self_critique(answer: str) -> str:
    llm = get_chat_model()
    resp = await llm.ainvoke([SystemMessage(content=_SYS), HumanMessage(content=answer)])
    return resp.content
