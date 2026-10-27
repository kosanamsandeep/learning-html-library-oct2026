"""P1 AI Engineering · Agentic Design Patterns.

Four reusable building blocks behind every "agent framework":

  1. Router       — pick which path/tool to use.
  2. Planner      — split a goal into ordered subtasks.
  3. ReAct loop   — reason -> act (call tool) -> observe -> repeat.
  4. Reflector    — critique the answer; iterate when not good enough.

The MockLLM here returns deterministic answers based on simple rules so the
script runs offline. Swap in a real LLM at the boundary later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

# ---------- mock LLM and toy tools ----------------------------------------


@dataclass
class MockLLM:
    """Pretend LLM whose responses are picked by keyword."""

    def complete(self, prompt: str) -> str:
        """Return a canned response based on words the prompt contains."""
        p = prompt.lower()
        if "route:" in p:
            if "weather" in p:
                return "weather_tool"
            if "math" in p or any(c in p for c in "+-*/"):
                return "math_tool"
            return "chat"
        if "plan:" in p:
            return (
                "1. fetch the user's city\n"
                "2. look up tomorrow's forecast\n"
                "3. write a one-line summary"
            )
        if "reflect:" in p:
            return (
                "answer is fine"
                if "celsius" in p or "result" in p
                else "answer is incomplete, retry with more detail"
            )
        if "react:" in p:
            if "thought-1" in p:
                return "Thought: I need the weather. Action: weather_tool(Bengaluru)"
            if "observation" in p:
                return "Thought: I have what I need. Final: Tomorrow in Bengaluru is 28C and sunny."
        return "ok"


def weather_tool(city: str) -> str:
    """Pretend weather lookup."""
    return f"{city}: 28C, sunny"


def math_tool(expression: str) -> str:
    """Evaluate a tiny arithmetic expression safely."""
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        raise ValueError("unsafe expression")
    return str(eval(expression))  # noqa: S307 - whitelisted chars only


TOOLS: dict[str, Callable[[str], str]] = {
    "weather_tool": weather_tool,
    "math_tool": math_tool,
}


# ---------- the four patterns ---------------------------------------------


@dataclass
class Router:
    """Pattern 1: pick which tool/path handles this request."""

    llm: MockLLM

    def route(self, user_input: str) -> str:
        """Return the name of the chosen tool or 'chat'."""
        return self.llm.complete(f"route: {user_input}")


@dataclass
class Planner:
    """Pattern 2: split a goal into ordered steps."""

    llm: MockLLM

    def plan(self, goal: str) -> list[str]:
        """Return a list of step descriptions."""
        raw = self.llm.complete(f"plan: {goal}")
        return [line.split(". ", 1)[1] for line in raw.splitlines() if ". " in line]


@dataclass
class ReActAgent:
    """Pattern 3: reason -> act -> observe loop."""

    llm: MockLLM
    max_steps: int = 4
    trace: list[str] = field(default_factory=list)

    def run(self, goal: str) -> str:
        """Iterate until the LLM emits 'Final:' or we hit the step cap."""
        scratchpad = f"react: thought-1 goal={goal}"
        for _ in range(self.max_steps):
            response = self.llm.complete(scratchpad)
            self.trace.append(response)
            if response.startswith("Thought:") and "Action:" in response:
                action = response.split("Action:")[1].strip()
                tool, _, arg = action.partition("(")
                arg = arg.rstrip(")")
                observation = TOOLS[tool](arg)
                self.trace.append(f"Observation: {observation}")
                scratchpad = f"react: observation {observation}"
            elif "Final:" in response:
                return response.split("Final:")[1].strip()
        return "(no final answer)"


@dataclass
class Reflector:
    """Pattern 4: critique an answer; retry when not good enough."""

    llm: MockLLM
    max_retries: int = 2

    def improve(self, draft: str, retry: Callable[[], str]) -> str:
        """Return draft when judged fine; otherwise call `retry` up to N times."""
        for _ in range(self.max_retries + 1):
            verdict = self.llm.complete(f"reflect: {draft}")
            if "fine" in verdict:
                return draft
            draft = retry()
        return draft


# ---------- demo ----------------------------------------------------------


def main() -> None:
    """Show each pattern in isolation, then combine them end-to-end."""
    llm = MockLLM()

    print("--- Pattern 1: Router ---")
    for q in ["what is the weather tomorrow?", "12 * 7 + 1", "hello there"]:
        print(f"  '{q}' -> {Router(llm).route(q)}")

    print("\n--- Pattern 2: Planner ---")
    for step in Planner(llm).plan("tell me tomorrow's forecast for my city"):
        print(f"  - {step}")

    print("\n--- Pattern 3: ReAct ---")
    agent = ReActAgent(llm)
    answer = agent.run("tomorrow's weather in Bengaluru")
    for line in agent.trace:
        print(f"  {line}")
    print(f"  => {answer}")

    print("\n--- Pattern 4: Reflector ---")
    drafts = iter(["short answer", "the result is 28 celsius, sunny"])
    final = Reflector(llm).improve(next(drafts), lambda: next(drafts))
    print(f"  final answer: {final}")


if __name__ == "__main__":
    main()
