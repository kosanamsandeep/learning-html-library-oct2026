"""ReAct research agent with 4 async tools."""
from __future__ import annotations

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import StructuredTool

from agents.base_agent import BaseAgent
from agents.skills import web_search, read_url, summarise, save_report
from core.config import settings
from core.logger import get_logger
from models.model_client import get_chat_model

log = get_logger(__name__)


def _load_prompt() -> PromptTemplate:
    text = (settings.prompts_dir / "react_research.txt").read_text(encoding="utf-8")
    return PromptTemplate.from_template(text)


class ResearchAgent(BaseAgent):
    name = "react-researcher"

    def __init__(self) -> None:
        self.llm = get_chat_model()
        self.tools = [
            StructuredTool.from_function(
                coroutine=web_search,
                name="web_search",
                description="Search the web. Input: a search query string.",
            ),
            StructuredTool.from_function(
                coroutine=read_url,
                name="read_url",
                description="Fetch one URL and return its main text. Input: a single URL.",
            ),
            StructuredTool.from_function(
                coroutine=summarise,
                name="summarise",
                description="Condense long text into a 200-word bullet digest. Input: the text.",
            ),
            StructuredTool.from_function(
                coroutine=save_report,
                name="save_report",
                description="Save markdown to disk under reports/. Input: the markdown string.",
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
        if not prompt.strip():
            return "Invalid prompt."
        log.info("research", extra={"prompt_len": len(prompt)})
        instruction = (
            f"Research the topic: '{prompt}'. Steps to follow strictly: "
            "(1) web_search for 3-5 URLs, "
            "(2) read_url on the 2 best URLs, "
            "(3) summarise the combined notes, "
            "(4) save_report. Return only the saved file path."
        )
        result = await self.executor.ainvoke({"input": instruction})
        return result["output"]
