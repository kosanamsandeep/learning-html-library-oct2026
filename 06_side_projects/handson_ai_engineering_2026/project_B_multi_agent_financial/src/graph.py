"""LangGraph multi-agent financial analyst.

Architecture: supervisor pattern.
  Supervisor → routes to one of: Researcher | Analyst | Writer | END.
"""
from __future__ import annotations
import os
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from .tools import ALL_TOOLS, get_price_history, get_company_fundamentals, web_search_news


# ---------- shared state ----------
class TeamState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next: str  # routing decision


# ---------- LLM ----------
def _llm(model: str | None = None, temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(
        model=model or os.getenv("LLM_MODEL", "gpt-5"),
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
    )


# ---------- worker agents ----------
researcher = create_react_agent(
    model=_llm(),
    tools=[web_search_news],
    prompt="You are a financial researcher. Gather the latest news, filings and "
           "market sentiment for the requested ticker. Return concise bullets.",
    name="researcher",
)

analyst = create_react_agent(
    model=_llm(),
    tools=[get_price_history, get_company_fundamentals],
    prompt="You are a quantitative analyst. Pull price history and fundamentals, "
           "compute simple metrics (30d return, volatility, PE comparison) and "
           "return a JSON-shaped insight block.",
    name="analyst",
)

writer = create_react_agent(
    model=_llm(temperature=0.2),
    tools=[],
    prompt="You are a sell-side report writer. Combine the researcher and "
           "analyst outputs into a structured report with sections: "
           "Summary, Bull Case, Bear Case, Verdict.",
    name="writer",
)


# ---------- supervisor ----------
class Route(BaseModel):
    next: Literal["researcher", "analyst", "writer", "FINISH"] = Field(
        ..., description="Which worker should act next, or FINISH if the report is complete.")


SUPERVISOR_SYS = (
    "You are the supervisor of a 3-agent financial team: researcher, analyst, "
    "writer. Decide the single next worker. Typical flow: researcher → analyst "
    "→ writer → FINISH. Do not repeat a worker unless instructed.")


def supervisor_node(state: TeamState) -> dict:
    llm = _llm().with_structured_output(Route)
    decision = llm.invoke(
        [SystemMessage(content=SUPERVISOR_SYS), *state["messages"]]
    )
    nxt = "END" if decision.next == "FINISH" else decision.next
    return {"next": nxt}


# ---------- graph ----------
def build_graph():
    g = StateGraph(TeamState)
    g.add_node("supervisor", supervisor_node)
    g.add_node("researcher", lambda s: {"messages": [researcher.invoke(s)["messages"][-1]]})
    g.add_node("analyst",    lambda s: {"messages": [analyst.invoke(s)["messages"][-1]]})
    g.add_node("writer",     lambda s: {"messages": [writer.invoke(s)["messages"][-1]]})

    g.add_edge(START, "supervisor")
    for worker in ("researcher", "analyst", "writer"):
        g.add_edge(worker, "supervisor")
    g.add_conditional_edges(
        "supervisor",
        lambda s: s["next"],
        {"researcher": "researcher", "analyst": "analyst",
         "writer": "writer", "END": END},
    )
    return g.compile()


def run(ticker: str) -> str:
    app = build_graph()
    result = app.invoke({
        "messages": [HumanMessage(content=f"Produce an investment report for {ticker}.")],
        "next": "researcher",
    })
    return result["messages"][-1].content


if __name__ == "__main__":
    import sys
    print(run(sys.argv[1] if len(sys.argv) > 1 else "AAPL"))
