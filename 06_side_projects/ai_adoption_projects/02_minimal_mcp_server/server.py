#!/usr/bin/env python3
"""
minimal_mcp_server.py — One MCP tool to search documentation.

Usage:
  # Run the server (stdio transport — default for Claude Code, Copilot, etc.)
  python server.py

  # Run with SSE transport (HTTP-based, for web clients)
  python server.py --transport sse --port 8000

  # Connect via Claude Code:
  claude mcp add docs-search -- python /path/to/server.py
"""

from __future__ import annotations
import json
import argparse
from pathlib import Path
from mcp.server import FastMCP

# ── Configuration ──────────────────────────────────────────────
HERE = Path(__file__).parent
DOCS_INDEX = HERE / "docs_index.json"


# ── Local search engine ────────────────────────────────────────
def _load_index() -> list[dict]:
    """Load the documentation index from the JSON file."""
    if not DOCS_INDEX.exists():
        return []
    with open(DOCS_INDEX) as f:
        return json.load(f)


def _search_local(query: str, top_k: int = 5) -> list[dict]:
    """
    Simple keyword-scored search over the local documentation index.

    Scores are computed as:
      - title match count × 3 (title matches are weighted higher)
      - content match count × 1
      - tag match count × 2
    """
    entries = _load_index()
    if not entries:
        return []

    query_lower = query.lower()
    scored: list[tuple[float, dict]] = []

    for entry in entries:
        score = 0.0
        title = entry.get("title", "")
        content = entry.get("content", "")
        tags = " ".join(entry.get("tags", []))

        score += title.lower().count(query_lower) * 3.0
        score += content.lower().count(query_lower) * 1.0
        score += tags.lower().count(query_lower) * 2.0

        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored[:top_k]]


# ── Create the MCP server ──────────────────────────────────────
mcp = FastMCP(
    name="Docs Search Server",
    instructions="Search technical documentation and return relevant results. "
    "Covers FastAPI, Python, Docker, Git, SQLAlchemy, Pytest, and Claude Code topics.",
)


@mcp.tool(
    description="Search documentation. Returns title + content body for each match."
)
def search_docs(
    query: str,
    top_k: int = 5,
) -> str:
    """
    Search the documentation index for the given query.

    Parameters
    ----------
    query : str
        The search term or phrase (e.g., "fastapi cors", "docker compose").
    top_k : int
        Maximum number of results to return (default 5, max 10).

    Returns
    -------
    str
        Formatted search results with titles and content snippets.
    """
    top_k = min(max(top_k, 1), 10)
    results = _search_local(query, top_k)

    if not results:
        return "No matching documentation found. Try a different query."

    lines: list[str] = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "Untitled")
        content = r.get("content", "")[:600]
        tags = ", ".join(r.get("tags", []))
        lines.append(
            f"**{i}. {title}**\n"
            f"   Tags: {tags}\n"
            f"   {content}\n"
        )

    return "\n".join(lines)


# ── Additional tools for a richer MCP server ───────────────────

@mcp.tool(
    description="List all available documentation topics and their tags. "
    "Use this to discover what's documented."
)
def list_topics() -> str:
    """List all indexed documentation topics."""
    entries = _load_index()
    if not entries:
        return "No documentation topics indexed."

    lines: list[str] = []
    for i, entry in enumerate(entries, 1):
        tags = ", ".join(entry.get("tags", []))
        lines.append(f"{i:>3}. {entry['title']}  [{tags}]")
    return "\n".join(lines)


@mcp.tool(
    description="Get the full content of a documentation topic by its exact title."
)
def get_topic(title: str) -> str:
    """
    Retrieve a documentation entry by its exact title.

    Parameters
    ----------
    title : str
        The exact title of the documentation topic.
    """
    entries = _load_index()
    for entry in entries:
        if entry["title"].lower() == title.lower():
            content = entry["content"]
            tags = ", ".join(entry.get("tags", []))
            return f"# {entry['title']}\n\nTags: {tags}\n\n{content}"
    return f"Topic '{title}' not found. Use list_topics() to see all available topics."


# ── Entry point ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Minimal MCP Documentation Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol (stdio for CLI agents, sse for HTTP)",
    )
    parser.add_argument("--port", type=int, default=8000, help="Port for SSE transport")
    args = parser.parse_args()

    print(f"🧩 Docs Search MCP Server starting...", file=__import__("sys").stderr)
    print(f"   Transport: {args.transport}", file=__import__("sys").stderr)
    print(f"   Tools: search_docs, list_topics, get_topic", file=__import__("sys").stderr)
    print(f"   Index: {DOCS_INDEX.name} ({len(_load_index())} entries)", file=__import__("sys").stderr)

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
