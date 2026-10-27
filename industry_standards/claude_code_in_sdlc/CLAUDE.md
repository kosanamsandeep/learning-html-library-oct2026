# Project: orders-service

## What this is
A toy order-management library. Pure Python, no framework. Used by the
industry_standards track to demonstrate how to wire Claude Code into a
working repo.

## Build & test
- Python 3.11+
- Install: `pip install -r requirements.txt`
- Run tests: `pytest -q`
- Lint: `ruff check .` (optional; not enforced in this sample)

## Conventions
- Type hints on every public function.
- AAA test layout (Arrange, Act, Assert).
- Money is stored as integer cents — never floats.
- No third-party deps in `src/` beyond what is in requirements.txt.

## Don't touch
- `src/orders.py:LEGACY_PRICE_RULES` — deprecation in flight, owned by the pricing team.

## When in doubt
- Ask before changing public function signatures.
- Open a PR; never push to main.
- If a test fails after your change, fix the code, not the test (unless
  the test was clearly wrong — and even then, justify it in the PR).

## Skills available in this repo
- `pytest-tdd` — see `.claude/skills/pytest-tdd/SKILL.md`. Activated when
  the request involves writing or fixing pytest tests.
