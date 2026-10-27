# Minimal MCP Server

A working Model Context Protocol (MCP) server that demonstrates how to expose tools to any MCP-compatible AI agent — Claude Code, Copilot, Cline, Continue.dev, and more.

## Quick Start

```bash
# 1. Activate the virtual environment
source .venv/bin/activate

# 2. Run the docs server
python server.py

# 3. In another terminal, test it
python test_client.py --server server.py
```

## Architecture

```
┌─────────────┐     JSON-RPC 2.0      ┌──────────────────┐
│  AI Agent    │ ◄────── stdio ──────► │   MCP Server     │
│ (Claude Code │                        │                  │
│  Copilot,    │                        │  search_docs()   │
│  Cline...)   │                        │  list_topics()   │
│              │                        │  get_topic()     │
└─────────────┘                        └──────┬───────────┘
                                              │
                                     ┌────────▼────────┐
                                     │  docs_index.json │
                                     │  (15 topics)     │
                                     └─────────────────┘
```

## What's in this project

| File | Purpose |
|------|---------|
| `server.py` | Docs search MCP server (3 tools) |
| `examples_server.py` | Multi-tool server with 6 progressive examples |
| `test_client.py` | Test client to exercise any MCP server |
| `docs_index.json` | Sample documentation index (15 topics) |
| `.venv/` | Python virtual environment with MCP SDK |

## Server 1: Docs Search (`server.py`)

Three tools that search a local documentation index:

```bash
# Run the server
source .venv/bin/activate
python server.py
```

### Tools

| Tool | Description | Example args |
|------|-------------|-------------|
| `search_docs(query, top_k)` | Search documentation by keyword | `query="fastapi cors"` |
| `list_topics()` | List all indexed topics | — |
| `get_topic(title)` | Get full content by exact title | `title="FastAPI — CORS Middleware"` |

### Sample query

```python
search_docs(query="docker compose", top_k=3)
# Returns:
# **1. Docker — docker-compose for Multi-Container Apps**
#    Docker Compose lets you define multi-container apps...
# **2. Docker — Dockerfile Best Practices**
#    Use multi-stage builds to keep images small...
```

## Server 2: Progressive Examples (`examples_server.py`)

Six tools at increasing complexity, designed as templates for your own MCP tools:

```bash
source .venv/bin/activate
python examples_server.py
```

### BASIC

| Tool | What it demonstrates |
|------|---------------------|
| `calculator(expression)` | Safe eval with restricted math context |
| `current_time(format)` | Simple parameter with enum (Literal) |

### INTERMEDIATE

| Tool | What it demonstrates |
|------|---------------------|
| `get_weather(city, units)` | Simulated external API (deterministic) |
| `text_stats(text)` | Pure computation with formatted output |
| `unit_convert(value, from_unit, to_unit)` | Lookup-table logic with broad coverage |

### ADVANCED

| Tool | What it demonstrates |
|------|---------------------|
| `review_code(input_data)` | Pydantic model as structured input + real analysis logic |

### Sample outputs

```python
calculator("sqrt(144) * 2 + 10")    # → 34.0
current_time("readable")             # → Tuesday, July 14, 2026 at 10:22:26 AM UTC
get_weather("Tokyo", "celsius")      # → 22°C, Scattered Showers
text_stats("Your text here...")      # → word count, reading time, vocabulary richness
unit_convert(100, "km", "mi")        # → 100 km = 62.1371 mi
```

### Code review output

The `review_code` tool checks for:
- Bare `except:` clauses
- Hardcoded passwords / API keys / tokens
- Missing function docstrings
- Lines exceeding 100 characters
- Files over 200 lines

## Connect to Claude Code

```bash
# Add the docs server
claude mcp add docs-search -- python /home/sande/workspace/2ndjuly_learning/06_side_projects/ai_adoption_projects/02_minimal_mcp_server/server.py

# Add the examples server
claude mcp add mcp-examples -- python /home/sande/workspace/2ndjuly_learning/06_side_projects/ai_adoption_projects/02_minimal_mcp_server/examples_server.py
```

Or add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "docs-search": {
      "command": "python",
      "args": ["/path/to/server.py"]
    },
    "mcp-examples": {
      "command": "python",
      "args": ["/path/to/examples_server.py"]
    }
  }
}
```

Then restart Claude Code. You can now say: _"Search the docs for FastAPI CORS"_ and Claude will use the `search_docs` tool automatically.

## Connect to other MCP clients

The same servers work with any MCP-compatible client:

- **GitHub Copilot** — configure via `.github/copilot-instructions.md`
- **Cline** — configure in VS Code settings under `cline.mcpServers`
- **Continue.dev** — configure in `~/.continue/config.json`
- **MCP Inspector** — `npx @modelcontextprotocol/inspector python server.py`

## Running tests

```bash
# Test the docs server
python test_client.py --server server.py

# Test the examples server
python test_client.py --server examples_server.py
```

## Building your own MCP tool

The pattern is always the same:

```python
from mcp.server import FastMCP

mcp = FastMCP(name="My Server")

@mcp.tool(description="What this tool does")
def my_tool(param1: str, param2: int = 42) -> str:
    """Your logic here."""
    return f"Result: {param1} x {param2}"

mcp.run(transport="stdio")
```

That's it. The `FastMCP` class handles:
- JSON-RPC protocol negotiation
- Tool schema generation (from Python type annotations)
- stdio or SSE transport
- Error handling and logging

## Key concepts learned

1. **MCP = one server, any agent** — write once, connect everywhere
2. **JSON-RPC 2.0 over stdio** — any language can implement it
3. **Tool schema from type hints** — Python annotations auto-generate JSON Schema
4. **Pydantic models as inputs** — structured data for complex tools
5. **Capability negotiation** — client and server agree on protocol version
