"""LangGraph StateGraph: plan -> (search -> read)* -> write -> save."""
from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

from agents.base_agent import BaseAgent
from agents.skills import web_search, read_url, save_report
from core.config import settings
from core.logger import get_logger
from models.model_client import get_chat_model

log = get_logger(__name__)


class ResearchState(TypedDict):
    topic: str
    plan: list[str]
    step_idx: int
    notes: Annotated[list[str], operator.add]
    report: str
    file_path: str


class ResearchGraphAgent(BaseAgent):
    name = "langgraph-researcher"

    def __init__(self) -> None:
        self.llm = get_chat_model()
        self.graph = self._build()

    # ----- node implementations -----
    async def _plan(self, state: ResearchState) -> dict:
        sys_p = (settings.prompts_dir / "plan.txt").read_text(encoding="utf-8")
        msg = await self.llm.ainvoke([
            SystemMessage(content=sys_p),
            HumanMessage(content=state["topic"]),
        ])
        plan = [q.strip("-* ").strip() for q in msg.content.splitlines() if q.strip()][:3]
        log.info(f"plan: {plan}")
        return {"plan": plan, "step_idx": 0, "notes": []}

    async def _search(self, state: ResearchState) -> dict:
        q = state["plan"][state["step_idx"]]
        urls = await web_search(q, max_results=3)
        return {"notes": [f"### Step {state['step_idx']+1}: {q}\nURLs: {urls}"]}

    async def _read(self, state: ResearchState) -> dict:
        last = state["notes"][-1]
        # quick parse of urls list rendered above
        import re
        urls = re.findall(r"'([^']+)'", last) or re.findall(r'"([^"]+)"', last)
        text = ""
        for u in urls[:1]:
            text += await read_url(u, max_chars=2500)
        return {"notes": [f"Excerpt:\n{text}\n"], "step_idx": state["step_idx"] + 1}

    def _route(self, state: ResearchState) -> str:
        return "search" if state["step_idx"] < len(state["plan"]) else "write"

    async def _write(self, state: ResearchState) -> dict:
        sys_w = (settings.prompts_dir / "write.txt").read_text(encoding="utf-8")
        msg = await self.llm.ainvoke([
            SystemMessage(content=sys_w),
            HumanMessage(content=f"Topic: {state['topic']}\n\nNotes:\n" + "\n\n".join(state["notes"])),
        ])
        return {"report": msg.content}

    async def _save(self, state: ResearchState) -> dict:
        path = await save_report(state["report"])
        return {"file_path": path}

    def _build(self):
        g = StateGraph(ResearchState)
        g.add_node("plan", self._plan)
        g.add_node("search", self._search)
        g.add_node("read", self._read)
        g.add_node("write", self._write)
        g.add_node("save", self._save)
        g.set_entry_point("plan")
        g.add_edge("plan", "search")
        g.add_edge("search", "read")
        g.add_conditional_edges("read", self._route, {"search": "search", "write": "write"})
        g.add_edge("write", "save")
        g.add_edge("save", END)
        return g.compile()

    async def run(self, prompt: str) -> dict:
        if not prompt.strip():
            return {"error": "empty topic"}
        final = await self.graph.ainvoke({
            "topic": prompt, "plan": [], "step_idx": 0,
            "notes": [], "report": "", "file_path": "",
        })
        return {"file_path": final["file_path"], "report": final["report"]}
