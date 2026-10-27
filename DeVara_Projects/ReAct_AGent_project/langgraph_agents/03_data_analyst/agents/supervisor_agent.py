"""Multi-agent Supervisor over Data-Analyst specialists.

Architecture:
    user → supervisor (LLM router) → one of:
        - sql_agent     (prebuilt ReAct, sql tools)
        - python_agent  (prebuilt ReAct, pandas + chart tools)
        - critic        (LLM grader)
        - END (when supervisor says FINISH)

State carries the running message list + a `next` field set by the supervisor.
"""
from __future__ import annotations

from typing import Annotated, Literal, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from agents.base_agent import BaseAgent
from agents.skills import list_tables, describe_table, run_sql, run_python, make_chart
from core.config import settings
from core.logger import get_logger
from models.model_client import get_chat_model

log = get_logger(__name__)


class Router(BaseModel):
    """Structured supervisor decision."""
    next: Literal["sql_agent", "python_agent", "critic", "FINISH"] = Field(
        ..., description="Which specialist should act next, or FINISH to return the answer."
    )


class State(MessagesState):
    next: str


class DataAnalystSupervisor(BaseAgent):
    name = "langgraph-analyst-supervisor"

    def __init__(self) -> None:
        self.llm = get_chat_model()

        # specialist agents (prebuilt ReAct)
        self.sql_agent = create_react_agent(
            model=self.llm,
            tools=[list_tables, describe_table, run_sql],
            prompt=(settings.prompts_dir / "sql_agent.txt").read_text(encoding="utf-8"),
        )
        self.python_agent = create_react_agent(
            model=self.llm,
            tools=[run_python, make_chart],
            prompt=(settings.prompts_dir / "python_agent.txt").read_text(encoding="utf-8"),
        )

        self.checkpointer = MemorySaver()
        self.graph = self._build()

    # ---- supervisor ----
    async def _supervisor(self, state: State) -> dict:
        sys_p = (settings.prompts_dir / "supervisor.txt").read_text(encoding="utf-8")
        msgs = [SystemMessage(content=sys_p)] + state["messages"]
        decision: Router = await self.llm.with_structured_output(Router).ainvoke(msgs)
        log.info(f"supervisor → {decision.next}")
        return {"next": decision.next}

    def _route(self, state: State) -> str:
        nxt = state["next"]
        return END if nxt == "FINISH" else nxt

    # ---- specialist wrappers ----
    async def _sql_node(self, state: State) -> dict:
        result = await self.sql_agent.ainvoke({"messages": state["messages"]})
        last = result["messages"][-1]
        return {"messages": [HumanMessage(content=f"[sql_agent]: {last.content}",
                                          name="sql_agent")]}

    async def _python_node(self, state: State) -> dict:
        result = await self.python_agent.ainvoke({"messages": state["messages"]})
        last = result["messages"][-1]
        return {"messages": [HumanMessage(content=f"[python_agent]: {last.content}",
                                          name="python_agent")]}

    async def _critic(self, state: State) -> dict:
        sys_p = (settings.prompts_dir / "critic.txt").read_text(encoding="utf-8")
        msg = await self.llm.ainvoke([SystemMessage(content=sys_p)] + state["messages"])
        return {"messages": [HumanMessage(content=f"[critic]: {msg.content}", name="critic")]}

    # ---- graph ----
    def _build(self):
        g = StateGraph(State)
        g.add_node("supervisor", self._supervisor)
        g.add_node("sql_agent", self._sql_node)
        g.add_node("python_agent", self._python_node)
        g.add_node("critic", self._critic)

        g.set_entry_point("supervisor")
        g.add_conditional_edges("supervisor", self._route, {
            "sql_agent": "sql_agent",
            "python_agent": "python_agent",
            "critic": "critic",
            END: END,
        })
        # all specialists report back to supervisor
        for n in ("sql_agent", "python_agent", "critic"):
            g.add_edge(n, "supervisor")
        return g.compile(checkpointer=self.checkpointer)

    async def run(self, prompt: str, thread_id: str = "default") -> str:
        if not prompt.strip():
            return "Invalid prompt."
        config = {"configurable": {"thread_id": thread_id}}
        final = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=prompt)]},
            config=config,
        )
        # last assistant message
        for m in reversed(final["messages"]):
            if isinstance(m, BaseMessage) and m.content:
                return m.content
        return ""
