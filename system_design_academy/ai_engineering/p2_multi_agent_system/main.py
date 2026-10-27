"""P2 AI Engineering · Multi-Agent System.

A supervisor agent routes work to specialist worker agents and aggregates
their results. This is the pattern behind LangGraph supervisor graphs,
CrewAI crews, and AutoGen group chats.

Workers here are tiny role-flavoured wrappers around a MockLLM:
  - Researcher: extracts facts from a knowledge base.
  - Writer:     turns facts into prose.
  - Critic:     red-pens the prose against the facts.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------- mock LLM ------------------------------------------------------

KB = {
    "consistent hashing": "Consistent hashing places servers on a ring of hash slots. Adding or removing one server only moves the slice of keys assigned to it. Virtual nodes keep load even.",
    "rate limiter": "A rate limiter caps request rate per client. Common algorithms: token bucket (allows bursts), sliding window log (exact), fixed window (cheap but bursty at boundaries).",
    "bloom filter": "A bloom filter answers set membership in O(1) with a small false positive rate using k hash functions and a bit array.",
}


class MockLLM:
    """Tiny role-aware mock LLM."""

    def respond(self, role: str, prompt: str) -> str:
        """Generate a canned response shaped by the agent's role."""
        if role == "researcher":
            for topic, fact in KB.items():
                if topic in prompt.lower():
                    return f"FACT[{topic}]: {fact}"
            return "FACT[unknown]: no fact found"
        if role == "writer":
            facts = [line for line in prompt.splitlines() if line.startswith("FACT")]
            body = (
                " ".join(line.split(": ", 1)[1] for line in facts)
                if facts
                else "(no content)"
            )
            return f"DRAFT: {body}"
        if role == "critic":
            if "FACT[unknown]" in prompt:
                return "CRITIQUE: missing source — reject."
            if "DRAFT:" in prompt and len(prompt) < 80:
                return "CRITIQUE: too short — ask writer to expand."
            return "CRITIQUE: ok"
        return "(no response)"


# ---------- agents --------------------------------------------------------


@dataclass
class Agent:
    """Named role + reference to the shared LLM."""

    name: str
    role: str
    llm: MockLLM

    def act(self, prompt: str) -> str:
        """Run one LLM call with the agent's role applied."""
        return self.llm.respond(self.role, prompt)


@dataclass
class Supervisor:
    """Coordinator that decides which worker runs next."""

    researcher: Agent
    writer: Agent
    critic: Agent

    def handle(self, user_question: str) -> str:
        """Run researcher -> writer -> critic, with one retry on a bad critique."""
        facts = self.researcher.act(user_question)
        print(f"  [{self.researcher.name}] {facts}")

        draft = self.writer.act(facts)
        print(f"  [{self.writer.name}] {draft}")

        critique = self.critic.act(draft)
        print(f"  [{self.critic.name}] {critique}")

        if "ok" not in critique.lower():
            # Retry with a stronger instruction (concatenate critique).
            draft = self.writer.act(
                f"{facts}\nNOTE: {critique}\nExpand to 2 sentences."
            )
            print(f"  [{self.writer.name} retry] {draft}")
        return draft


def main() -> None:
    """Run two example questions through the supervisor pipeline."""
    llm = MockLLM()
    sup = Supervisor(
        researcher=Agent("research", "researcher", llm),
        writer=Agent("write", "writer", llm),
        critic=Agent("critic", "critic", llm),
    )

    for question in [
        "explain consistent hashing in one paragraph",
        "what is a bloom filter?",
    ]:
        print(f"\nuser: {question}")
        final = sup.handle(question)
        print(f"=> final: {final}")


if __name__ == "__main__":
    main()
