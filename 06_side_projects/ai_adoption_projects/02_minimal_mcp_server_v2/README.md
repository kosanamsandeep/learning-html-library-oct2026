# MCP + LangGraph — Code Review Agent Demo

A runnable demo showing how **MCP (Model Context Protocol)** and **LangGraph** work together.

```
┌─────────────────────────────────────────────────────┐
│  LangGraph (orchestration)                          │
│  • Defines the workflow steps & their order         │
│  • Manages state between steps                      │
│  • Fans out to parallel analyzers via Send()       │
│  • Fans in at join nodes                            │
│                                                     │
│  ↓ calls tools via MCP protocol ↓                   │
│                                                     │
│  MCP Server (tool provider)                         │
│  • Exposes tools: read_file, analyze, check, format │
│  • Each tool is self-contained, language-agnostic   │
│  • Same server works with ANY MCP-speaking agent    │
└─────────────────────────────────────────────────────┘
```

## Quick Start

```bash
cd langgraph-mcp-demo
pip install -r requirements.txt
python main.py
```

To review a different file:
```bash
python main.py path/to/your/file.py
```

## What You'll See

```
╔══════════════════════════════════════════════════════╗
║   MCP + LangGraph — Code Review Agent Demo          ║
╚══════════════════════════════════════════════════════╝

🔌 [1/4] Starting MCP server (code-review-tools)...
       ✅ Connected and session initialized

🔎 [2/4] Discovering MCP tools...
       Found 5 tools:
       • read_source_file
       • analyze_syntax
       • check_dependencies
       • check_code_style
       • format_report

🧠 [3/4] Building LangGraph workflow...
   ╔══ LangGraph Structure ═══════════════════════╗
   ║  read_file → ['analyze_syntax', 'check_deps', 'check_style']
   ║  analyze_syntax → ['gather_results']
   ║  check_deps → ['gather_results']
   ║  check_style → ['gather_results']
   ║  gather_results → ['generate_report']
   ║  generate_report → ['END']
   ╚═══════════════════════════════════════════════╝

📂 [4/4] Reviewing: vulnerable_code.py
       ──────────────────────────────────────────────────
  📂 [read_file] Reading sample_code/vulnerable_code.py...
     ✅ Loaded 1478 characters
  🔍 [analyze_syntax] Parsing AST...
     Valid syntax: True, Functions: 4, Classes: 1
  📦 [check_deps] Scanning imports...
     Found 2 imports
  ✨ [check_style] Running style checks...
     Found 6 style issues
  🔗 [gather_results] Joining parallel results...
  📝 [generate_report] Building report...
       ──────────────────────────────────────────────────

# 📋 Code Review Report: `vulnerable_code.py`

## 🔴 Defects (Must Fix)
- ❌ Risky dependency: `pickle` – Unsafe deserialization...
- ❌ Risky dependency: `eval` – Code injection risk...

## 🟡 Warnings (Should Fix)
- ⚠️ Found 2 bare 'except:' clause(s) – catches ALL exceptions
- ⚠️ Style: Line 15: trailing whitespace
- ⚠️ Style: Line 46: 133 chars exceeds 100 limit
- ⚠️ Style: Line 7: class 'user_data_handler' should be PascalCase
- ⚠️ Style: Line 13: function 'SaveToCache' should be snake_case
- ⚠️ Style: Line 27: function 'LoadConfig' should be snake_case
- ⚠️ Style: Line 37: function 'SaveSession' should be snake_case

## ✅ Passed Checks
- ✅ Python syntax is valid (AST parsed successfully)
- ✅ Dependencies scanned: 2 imports found

**Summary:** 2 defects, 7 warnings, 2 checks passed
```

## Architecture in 2 Minutes

### MCP Server (`server/mcp_server.py`)
A standalone Python script that declares 5 tools. It runs as a subprocess and talks JSON-RPC over stdin/stdout. **It doesn't know or care about LangGraph.** Any MCP client can use it.

### MCP Client (`agent/mcp_client.py`)
Wraps the MCP protocol in an async context manager. Spawns the server, connects, discovers tools, and provides a `call_tool()` method.

### LangGraph Workflow (`agent/graph.py`)
Defines a state machine with 6 nodes. Three of them run in **parallel** (Send-based fan-out), then a join node collects results. Each node calls MCP tools.

### The Decoupling
- The **LangGraph agent never imports** a file reader, AST parser, or markdown formatter.
- The **MCP server doesn't know** about LangGraph, state management, or workflow orchestration.
- They meet at the **protocol layer** — MCP's JSON-RPC over stdio.

## Try These Modifications

1. **Point it at your own code**: `python main.py ../../my_project/app.py`
2. **Add a tool to the MCP server**: Add a new `Tool()` entry + handler in `mcp_server.py`
3. **Swap the MCP server**: Point `MCPClient` at a different server script
4. **Change the graph**: Add a new node to `graph.py` (e.g., `security_scan`)

## Prerequisites

- Python 3.10+
- `pip install mcp langgraph`
