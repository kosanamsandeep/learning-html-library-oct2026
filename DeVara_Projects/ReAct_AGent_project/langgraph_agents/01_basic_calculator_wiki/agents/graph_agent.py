"""LangGraph prebuilt ReAct agent with async tools + checkpointer for thread memory."""
from __future__ import annotations

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from agents.base_agent import BaseAgent
from agents.skills import calculator, wiki
from core.config import settings
from core.logger import get_logger
from models.model_client import get_chat_model

log = get_logger(__name__)


class LGCalcWikiAgent(BaseAgent):
    name = "langgraph-calc-wiki"

    def __init__(self) -> None:
        self.llm = get_chat_model()
        self.checkpointer = MemorySaver()
        prompt = (settings.prompts_dir / "system.txt").read_text(encoding="utf-8")
        self.graph = create_react_agent(
            model=self.llm,
            tools=[calculator, wiki],
            checkpointer=self.checkpointer,
            prompt=prompt,
        )

    async def run(self, prompt: str, thread_id: str = "default") -> str:
        if not prompt.strip():
            return "Invalid prompt."
        log.info("graph.invoke", extra={"thread_id": thread_id})
        config = {"configurable": {"thread_id": thread_id}}
        result = await self.graph.ainvoke(
            {"messages": [("user", prompt)]},
            config=config,
        )
        return result["messages"][-1].content
