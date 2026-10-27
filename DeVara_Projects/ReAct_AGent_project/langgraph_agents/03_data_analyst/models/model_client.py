from __future__ import annotations
from langchain_openai import ChatOpenAI
from core.config import settings


def get_chat_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=settings.temperature,
        api_key=settings.openai_api_key or None,
    )
