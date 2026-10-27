"""Self-reflective agentic RAG (LangGraph).

State machine:
  retrieve -> grade
    |- relevant -> generate -> hallucination_check
    |              |- grounded -> answer_quality
    |              |              |- good     -> END
    |              |              |- not_good -> rewrite_query -> retrieve
    |              |- not_grounded -> generate (re-prompt)
    |- not_relevant -> rewrite_query -> retrieve
"""
from __future__ import annotations
import os
from typing import Annotated, List, Literal, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from .retriever import Doc, SimpleRetriever


# ---------- shared state ----------
class RagState(TypedDict):
    question: str
    rewritten_question: str | None
    docs: List[Doc]
    answer: str | None
    relevance_ok: bool | None
    grounded_ok: bool | None
    quality_ok: bool | None
    iterations: int
    messages: Annotated[list[BaseMessage], add_messages]


def _llm(temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-5"),
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
    )


# ---------- graders ----------
class YesNo(BaseModel):
    yes: bool = Field(..., description="True if the criterion is met.")
    rationale: str = ""


def grade_relevance(state: RagState) -> dict:
    q = state.get("rewritten_question") or state["question"]
    ctx = "\n\n".join(d.text for d in state["docs"])
    llm = _llm().with_structured_output(YesNo)
    res: YesNo = llm.invoke([
        SystemMessage(content="Are the retrieved passages relevant enough to "
                              "answer the question? Reply yes/no."),
        HumanMessage(content=f"Question: {q}\n\nPassages:\n{ctx}")])
    return {"relevance_ok": res.yes}


def grade_groundedness(state: RagState) -> dict:
    ctx = "\n\n".join(d.text for d in state["docs"])
    llm = _llm().with_structured_output(YesNo)
    res = llm.invoke([
        SystemMessage(content="Is the answer fully supported by the passages "
                              "(no hallucinations)?"),
        HumanMessage(content=f"Passages:\n{ctx}\n\nAnswer:\n{state['answer']}")])
    return {"grounded_ok": res.yes}


def grade_quality(state: RagState) -> dict:
    q = state.get("rewritten_question") or state["question"]
    llm = _llm().with_structured_output(YesNo)
    res = llm.invoke([
        SystemMessage(content="Does the answer fully address the user's "
                              "question?"),
        HumanMessage(content=f"Question: {q}\nAnswer: {state['answer']}")])
    return {"quality_ok": res.yes}


# ---------- workers ----------
def make_retrieve_node(retriever: SimpleRetriever):
    def _node(state: RagState) -> dict:
        q = state.get("rewritten_question") or state["question"]
        docs = retriever.search(q, k=4)
        return {"docs": docs, "iterations": state.get("iterations", 0) + 1}
    return _node


def rewrite_query(state: RagState) -> dict:
    llm = _llm(temperature=0.3)
    new_q = llm.invoke([
        SystemMessage(content="Rewrite the user question to retrieve better "
                              "passages. Reply with ONLY the new question."),
        HumanMessage(content=state["question"])]).content
    return {"rewritten_question": str(new_q).strip()}


def generate(state: RagState) -> dict:
    q = state.get("rewritten_question") or state["question"]
    ctx = "\n\n".join(f"[{d.id}] {d.text}" for d in state["docs"])
    llm = _llm()
    out = llm.invoke([
        SystemMessage(content="Answer the question using ONLY the passages. "
                              "Cite [doc_id] for each claim."),
        HumanMessage(content=f"Question: {q}\n\nPassages:\n{ctx}")]).content
    return {"answer": str(out)}


# ---------- routers ----------
def route_after_relevance(state: RagState) -> Literal["generate", "rewrite", "give_up"]:
    if state["relevance_ok"]:
        return "generate"
    return "rewrite" if state["iterations"] < 3 else "give_up"


def route_after_grounded(state: RagState) -> Literal["check_quality", "regenerate"]:
    return "check_quality" if state["grounded_ok"] else "regenerate"


def route_after_quality(state: RagState) -> Literal["end", "rewrite", "give_up"]:
    if state["quality_ok"]:
        return "end"
    return "rewrite" if state["iterations"] < 3 else "give_up"


# ---------- graph factory ----------
def build_graph(retriever: SimpleRetriever):
    g = StateGraph(RagState)
    g.add_node("retrieve",      make_retrieve_node(retriever))
    g.add_node("grade_rel",     grade_relevance)
    g.add_node("rewrite",       rewrite_query)
    g.add_node("generate",      generate)
    g.add_node("grade_ground",  grade_groundedness)
    g.add_node("grade_quality", grade_quality)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "grade_rel")
    g.add_conditional_edges("grade_rel", route_after_relevance,
                            {"generate": "generate",
                             "rewrite":  "rewrite",
                             "give_up":  END})
    g.add_edge("rewrite", "retrieve")
    g.add_edge("generate", "grade_ground")
    g.add_conditional_edges("grade_ground", route_after_grounded,
                            {"check_quality": "grade_quality",
                             "regenerate":    "generate"})
    g.add_conditional_edges("grade_quality", route_after_quality,
                            {"end":     END,
                             "rewrite": "rewrite",
                             "give_up": END})
    return g.compile()
