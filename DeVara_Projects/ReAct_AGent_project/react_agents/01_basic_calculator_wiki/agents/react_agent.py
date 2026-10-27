"""ReAct agent that uses the calculator + wikipedia skills."""
from __future__ import annotations

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import StructuredTool

from agents.base_agent import BaseAgent
from agents.skills import calculate, wiki_summary
from core.config import settings
from core.logger import get_logger
from models.model_client import get_chat_model

log = get_logger(__name__)


def _load_prompt() -> PromptTemplate:
    template = (settings.prompts_dir / "react_system.txt").read_text(encoding="utf-8")
    return PromptTemplate.from_template(template)


class ReactCalcWikiAgent(BaseAgent):
    name = "react-calc-wiki"

    def __init__(self) -> None:
        self.llm = get_chat_model()
        self.tools = [
            StructuredTool.from_function(
                coroutine=calculate,
                name="calculator",
                description="Evaluate arithmetic. Input: a math expression like '23*45+1'.",
            ),
            StructuredTool.from_function(
                coroutine=wiki_summary,
                name="wikipedia",
                description="Look up a Wikipedia summary. Input: a short search query.",
            ),
        ]
        agent = create_react_agent(self.llm, self.tools, _load_prompt())
        self.executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=settings.verbose,
            handle_parsing_errors=True,
            max_iterations=settings.max_iterations,
        )

    async def run(self, prompt: str) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            return "Invalid prompt."
        log.info("agent.run", extra={"agent": self.name, "prompt_len": len(prompt)})
        result = await self.executor.ainvoke({"input": prompt})
        return result["output"]
