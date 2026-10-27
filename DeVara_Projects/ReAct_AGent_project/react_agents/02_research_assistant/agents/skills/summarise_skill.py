"""LLM-powered async summariser."""
from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage
from models.model_client import get_chat_model

_SYSTEM = (
    "You are a concise research analyst. Output a 200-word markdown digest "
    "with bullet points and inline citations like [1], [2]."
)


async def summarise(text: str) -> str:
    llm = get_chat_model()
    msgs = [SystemMessage(content=_SYSTEM), HumanMessage(content=f"Notes:\n\n{text}")]
    resp = await llm.ainvoke(msgs)
    return resp.content
