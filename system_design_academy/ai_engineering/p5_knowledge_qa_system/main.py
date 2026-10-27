"""P5 AI Engineering · Knowledge Q&A with Evaluation and Guardrails.

A production RAG system is not just retrieve + LLM. It needs:

  - Retrieval over a corpus.
  - Generation grounded in the retrieved sources (cite the source ids).
  - Guardrails: refuse out-of-scope or unsafe questions.
  - Evaluation: an automated check that the answer is supported by the
    sources (LLM-as-judge pattern, faked here with a deterministic rule).

This file ties them all together with a stdlib-only mock and a tiny corpus.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

# ---------- corpus & retrieval -------------------------------------------

CORPUS: list[tuple[str, str]] = [
    (
        "doc-1",
        "Consistent hashing places servers on a ring of hash slots. Adding or removing one server only re-maps the slice of keys owned by that server.",
    ),
    (
        "doc-2",
        "A bloom filter answers set membership in constant time with a small false positive rate using k hash functions and a bit array.",
    ),
    (
        "doc-3",
        "Token bucket rate limiters allow short bursts up to a bucket capacity and then enforce a steady refill rate over time.",
    ),
    (
        "doc-4",
        "The saga pattern coordinates a multi-step distributed transaction by running compensating actions in reverse order when a step fails.",
    ),
]


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens for the bag-of-words index."""
    return re.findall(r"[a-z0-9]+", text.lower())


def cosine(a: Counter[str], b: Counter[str]) -> float:
    """Cosine similarity between two bag-of-words vectors."""
    common = set(a) & set(b)
    num = sum(a[t] * b[t] for t in common)
    da = math.sqrt(sum(v * v for v in a.values()))
    db = math.sqrt(sum(v * v for v in b.values()))
    return num / (da * db) if da and db else 0.0


@dataclass
class Retriever:
    """Tiny bag-of-words 'vector store' for the demo."""

    docs: list[tuple[str, str]] = field(default_factory=lambda: list(CORPUS))
    _vecs: list[tuple[str, str, Counter[str]]] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        """Pre-compute one bag-of-words vector per document."""
        self._vecs = [(i, t, Counter(tokenize(t))) for i, t in self.docs]

    def top_k(self, query: str, k: int = 2) -> list[tuple[str, str, float]]:
        """Return the k most similar (id, text, score) tuples."""
        q = Counter(tokenize(query))
        scored = [(doc_id, text, cosine(q, vec)) for doc_id, text, vec in self._vecs]
        scored.sort(key=lambda x: x[2], reverse=True)
        return [s for s in scored[:k] if s[2] > 0]


# ---------- guardrails ----------------------------------------------------

BANNED = {"medical advice", "legal advice", "investment advice"}


def is_in_scope(question: str) -> bool:
    """Reject prompts that ask for restricted advice categories."""
    q = question.lower()
    return not any(b in q for b in BANNED)


# ---------- generation + evaluation --------------------------------------


@dataclass
class GroundedAnswerer:
    """Build an answer that cites doc ids and stays inside the retrieved text."""

    def answer(self, question: str, sources: list[tuple[str, str, float]]) -> str:
        """Return either a grounded answer or an explicit 'cannot answer' note."""
        if not sources:
            return "I do not have a source for that question."
        # The 'generation' here just stitches the top source's text + citation.
        doc_id, text, _ = sources[0]
        return f"{text} [source: {doc_id}]"


@dataclass
class AnswerEvaluator:
    """Faithfulness check: every claim word in the answer must appear in a source."""

    def grade(
        self, answer: str, sources: list[tuple[str, str, float]]
    ) -> tuple[float, str]:
        """Return (score 0..1, verdict text)."""
        # Strip the citation footer for the check.
        body = re.sub(r"\[source:[^\]]+\]", "", answer).lower()
        source_words = Counter()
        for _, text, _ in sources:
            source_words.update(tokenize(text))
        answer_words = [w for w in tokenize(body) if len(w) > 3]
        if not answer_words:
            return 0.0, "empty answer"
        grounded = sum(1 for w in answer_words if source_words[w])
        score = grounded / len(answer_words)
        verdict = (
            "grounded"
            if score >= 0.8
            else "partially grounded" if score >= 0.5 else "not grounded"
        )
        return round(score, 2), verdict


# ---------- orchestration ------------------------------------------------


@dataclass
class KnowledgeQA:
    """End-to-end: guardrail → retrieve → answer → evaluate."""

    retriever: Retriever = field(default_factory=Retriever)
    answerer: GroundedAnswerer = field(default_factory=GroundedAnswerer)
    evaluator: AnswerEvaluator = field(default_factory=AnswerEvaluator)

    def ask(self, question: str) -> dict:
        """Run the full pipeline and return a structured result."""
        if not is_in_scope(question):
            return {
                "answer": "Sorry, I can't help with that.",
                "score": None,
                "verdict": "refused",
            }
        sources = self.retriever.top_k(question, k=2)
        answer = self.answerer.answer(question, sources)
        score, verdict = self.evaluator.grade(answer, sources)
        return {
            "answer": answer,
            "sources": [s[0] for s in sources],
            "score": score,
            "verdict": verdict,
        }


def main() -> None:
    """Ask three questions: one good, one out-of-corpus, one banned."""
    qa = KnowledgeQA()
    for question in [
        "how does consistent hashing reduce key re-mapping?",
        "what is the population of Saturn?",
        "give me medical advice for a headache",
    ]:
        print(f"\nQ: {question}")
        result = qa.ask(question)
        for k, v in result.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
