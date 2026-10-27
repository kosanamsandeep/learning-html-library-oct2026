# Project: review-bot

## What this is
A small example of an automated code reviewer built with the OpenAI Agents
SDK. Used by the industry_standards track to demonstrate Codex CLI and the
Agents SDK on the same repo.

## Build & test
- Python 3.11+
- Install: `pip install -r requirements.txt`
- Run smoke tests: `pytest -q`
- (Live agent run requires `OPENAI_API_KEY` — not needed for the smoke tests.)

## Conventions
- Type hints on every public function.
- Tool functions live next to the agent that owns them.
- File paths passed to tools must be **absolute** — relative paths broke
  Anthropic's SWE-bench agent when it changed directory; we don't make
  the same mistake.
- Each tool has a junior-developer docstring: when to use, when not to use,
  and at least one example.

## Don't touch
- `src/reviewer.py:SYSTEM_PROMPT` — owned by the prompt-eval CI job.

## When in doubt
- Open a PR; never push to main.
- Don't run tools against production data from this repo. The reviewer
  is allowed to read diffs and run tests — nothing else.

## Surfaces
- Codex CLI reads this file automatically.
- The Agents SDK code in `src/reviewer.py` injects the conventions section
  into its system prompt at runtime.
