# MCP + LangGraph — Code Review Agent Demo

**Goal:** A runnable demo showing MCP (Model Context Protocol) and LangGraph working together — an MCP server exposes code-review tools, a LangGraph workflow orchestrates them with parallel analysis.

## Quick Start

```bash
pip install -r requirements.txt
python main.py
# Or review a specific file:
python main.py path/to/file.py
```

## Architecture

```
main.py → MCPClient → stdio JSON-RPC → MCP Server (5 tools)
       ↘
        LangGraph StateGraph (6 nodes, parallel Send-based fan-out)
         → reads file → checks syntax + deps + style (parallel)
         → gathers results → generates report
```

- **MCP Server** (`server/mcp_server.py`): Exposes 5 tools (read, syntax, deps, style, format). Language-agnostic — any MCP client can use it.
- **LangGraph Agent** (`agent/graph.py`): Defines the workflow — reads a file, fans out 3 parallel analyzers via `Send()`, joins at `gather_results`, generates the report.
- **MCP Client** (`agent/mcp_client.py`): Wraps the MCP protocol — spawns server as subprocess, discovers tools, handles cleanup.

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point — starts MCP server, builds graph, runs review |
| `server/mcp_server.py` | MCP server — 5 code-review tools over stdio JSON-RPC |
| `agent/mcp_client.py` | MCP client wrapper — handles session lifecycle |
| `agent/graph.py` | LangGraph StateGraph — 6 nodes with parallel fan-out |
| `sample_code/vulnerable_code.py` | Python file with deliberate issues for testing |

## Commands

| What | How |
|------|-----|
| Run the demo | `python main.py` |
| Review a file | `python main.py path/to/file.py` |
| MCP server standalone | `python server/mcp_server.py` (runs over stdio) |

## Learning Path

1. Run `python main.py` — see MCP + LangGraph working together
2. Add a new tool in `server/mcp_server.py` (e.g., `check_security`) — it auto-appears in the tool list
3. Modify `agent/graph.py` — add a node, change the parallel branches
4. Point the MCP client at a different MCP server to see the decoupling

## How MCP + LangGraph Complement Each Other

- **MCP** = tool discovery + invocation protocol. "What can you do?"
- **LangGraph** = workflow orchestration + state management. "In what order, and what runs in parallel?"
- They meet at the **tool call** — LangGraph nodes call MCP tools, MCP servers don't know about LangGraph.

## Notes

- The cleanup "cancel scope" warning on exit is a harmless known MCP SDK issue with cross-task session close — handled gracefully.
