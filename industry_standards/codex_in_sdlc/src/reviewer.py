"""Code-reviewer agent template (OpenAI Agents SDK).

This module is a *template* — it shows how a small reviewer agent is
structured using the OpenAI Agents SDK, with three function tools and an
explicit stop condition. Running ``main()`` requires the ``openai-agents``
package and an ``OPENAI_API_KEY``; the smoke tests in ``tests/`` exercise
just the pure-Python helpers and skip the live call.

Key conventions from ``AGENTS.md`` enforced here:

* **Absolute paths** — every tool that takes a path requires it to be
  absolute. Catches the relative-path failure mode early.
* **Junior-developer docstrings** — each tool's docstring tells the model
  when to use it, when not to, and shows an example.
* **Explicit stop** — the agent calls ``finish_review`` to return its
  final text, instead of relying on the runner to guess it is done.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

# The Agents SDK is optional at import time so the smoke tests can run
# without it. The actual ``main()`` function imports it lazily.


SYSTEM_PROMPT = """\
You are a senior Python reviewer for the review-bot repo. Read the diff
the user provides, run the project's tests, then call ``finish_review``
with a structured comment list.

Rules:
* Cite line numbers from the diff in every comment.
* Tag each comment as one of: BUG, RISK, NIT.
* Never propose a change that would silently weaken a test.
* Stop after at most three tool calls.
"""


# --- pure-Python helpers (also exposed as @function_tool in main) ---


def _require_absolute(path: str) -> Path:
    """Return ``Path(path)`` if it is absolute; raise ``ValueError`` otherwise.

    Tools rely on this so that a relative path like ``"src/foo.py"`` never
    silently resolves against the agent's current working directory.
    """
    p = Path(path)
    if not p.is_absolute():
        raise ValueError(f"path must be absolute, got {path!r}")
    return p


def read_diff_impl(path: str) -> str:
    """Read a unified diff from disk and return it as a string."""
    return _require_absolute(path).read_text(encoding="utf-8")


def run_tests_impl(working_dir: str) -> dict[str, Any]:
    """Run ``pytest -q`` in ``working_dir`` and return its outcome."""
    cwd = _require_absolute(working_dir)
    completed = subprocess.run(
        ["pytest", "-q"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "exit_code": completed.returncode,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def finish_review_impl(comments: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap the agent's final list of comments into a structured result."""
    return {"comments": comments, "count": len(comments)}


# --- live entry point (uses the Agents SDK) ---


def main(diff_path: str, repo_root: str) -> dict[str, Any]:
    """Run the reviewer agent on ``diff_path`` against ``repo_root``.

    Imports ``openai-agents`` lazily so the smoke tests do not require it
    to be installed. Requires ``OPENAI_API_KEY`` to be set in the env.
    """
    from agents import Agent, Runner, function_tool  # type: ignore[import-not-found]

    @function_tool
    def read_diff(path: str) -> str:
        """Read a unified diff from disk and return it as a string.

        USE THIS TOOL once at the start of the review to load the diff.
        DO NOT use it for anything other than the diff path the user gave you.

        Args:
            path: Absolute filesystem path to the diff. Must be absolute.

        Example:
            read_diff("/repo/changes/PR-42.patch")
        """
        return read_diff_impl(path)

    @function_tool
    def run_tests(working_dir: str) -> dict[str, Any]:
        """Run ``pytest -q`` in ``working_dir``.

        USE THIS TOOL after reading the diff to confirm the tests pass.
        DO NOT use it more than once per review.

        Args:
            working_dir: Absolute path to the repo root.

        Returns:
            ``{"exit_code", "stdout_tail", "stderr_tail"}``
        """
        return run_tests_impl(working_dir)

    @function_tool
    def finish_review(comments: list[dict[str, Any]]) -> dict[str, Any]:
        """Submit the final list of review comments and stop.

        USE THIS TOOL exactly once, at the end. After this call, the
        review is complete.

        Args:
            comments: A list of ``{line: int, tag: "BUG"|"RISK"|"NIT", text: str}``.
        """
        return finish_review_impl(comments)

    agent = Agent(
        name="Reviewer",
        instructions=SYSTEM_PROMPT,
        tools=[read_diff, run_tests, finish_review],
    )

    user_msg = (
        f"Review the diff at {diff_path}. "
        f"After running tests, call finish_review with at most 5 comments."
    )
    result = Runner.run_sync(agent, user_msg, max_turns=5)
    return {"final_output": result.final_output}


if __name__ == "__main__":  # pragma: no cover - CLI entry
    import sys

    if len(sys.argv) != 4 or sys.argv[1] != "review":
        print("usage: python -m src.reviewer review <abs-diff-path> <abs-repo-root>")
        raise SystemExit(2)

    out = main(sys.argv[2], sys.argv[3])
    print(out["final_output"])
