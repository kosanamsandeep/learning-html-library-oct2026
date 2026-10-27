"""Data Analyst ReAct agent with per-session memory."""
from __future__ import annotations

from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import StructuredTool

from agents.base_agent import BaseAgent
from agents.skills import (
    list_tables, describe_table, run_sql,
    run_python, make_chart, self_critique,
)
from core.config import settings
from core.logger import get_logger
from models.model_client import get_chat_model

log = get_logger(__name__)


def _load_prompt() -> PromptTemplate:
    text = (settings.prompts_dir / "react_analyst.txt").read_text(encoding="utf-8")
    return PromptTemplate.from_template(text)


def _tools() -> list[StructuredTool]:
    return [
        StructuredTool.from_function(coroutine=list_tables, name="list_tables",
            description="List tables in SQLite. No input needed."),
        StructuredTool.from_function(coroutine=describe_table, name="describe_table",
            description="Show columns + 5 sample rows. Input: table name (default 'data')."),
        StructuredTool.from_function(coroutine=run_sql, name="run_sql",
            description="Run a SELECT query on SQLite. Input: SQL string. Up to 50 rows."),
        StructuredTool.from_function(coroutine=run_python, name="run_python",
            description="Run pandas code on `df`. Set `result` variable to return a value."),
        StructuredTool.from_function(coroutine=make_chart, name="make_chart",
            description="Render PNG chart. Input format: 'kind|x|y' or 'kind|x|y|groupby'."),
        StructuredTool.from_function(coroutine=self_critique, name="self_critique",
            description="Grade your draft final answer before returning. Input: draft string."),
    ]


class DataAnalystAgent(BaseAgent):
    name = "react-data-analyst"

    def __init__(self) -> None:
        self.llm = get_chat_model()
        self.tools = _tools()
        self._executors: dict[str, AgentExecutor] = {}
        self._prompt = _load_prompt()

    def _executor_for(self, session_id: str) -> AgentExecutor:
        if session_id in self._executors:
            return self._executors[session_id]
        memory = ConversationBufferMemory(memory_key="chat_history", input_key="input")
        agent = create_react_agent(self.llm, self.tools, self._prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=memory,
            verbose=settings.verbose,
            handle_parsing_errors=True,
            max_iterations=settings.max_iterations,
        )
        self._executors[session_id] = executor
        return executor

    async def run(self, prompt: str, session_id: str = "default") -> str:
        if not prompt.strip():
            return "Invalid prompt."
        log.info("analyst.run", extra={"sid": session_id})
        result = await self._executor_for(session_id).ainvoke({"input": prompt})
        return result["output"]
