"""
╔══════════════════════════════════════════════════════════════════╗
║  LANGGRAPH WORKFLOW: Code Review Agent                          ║
║                                                                ║
║  This is the orchestration layer. It uses LangGraph's StateGraph ║
║  to define a multi-step workflow that calls MCP tools.           ║
║                                                                ║
║  Graph structure:                                               ║
║                                                                ║
║    START → read_file                                             ║
║                │                                                 ║
║                ├─→ analyze_syntax ──┐                            ║
║                ├─→ check_deps ──────┤─→ gather_results            ║
║                └─→ check_style ────┘     │                       ║
║                                          ↓                       ║
║                                     generate_report → END        ║
║                                                                ║
║  Key LangGraph concepts demonstrated:                           ║
║  • StateGraph with typed state                                  ║
║  • Parallel fan-out via Send()                                  ║
║  • Fan-in (join) via node with multiple incoming edges          ║
║  • Conditional edges                                            ║
║  • Async nodes (to support MCP's async protocol)               ║
╚══════════════════════════════════════════════════════════════════╝
"""
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from .mcp_client import MCPClient


# ─── State Definition ───
# LangGraph passes this dict-like object between nodes.
# Each node returns a partial update that gets merged into the state.
class ReviewState(TypedDict):
    # Input
    file_path: str

    # Populated by read_file
    content: Optional[str]
    read_error: Optional[str]

    # Populated by analyze_syntax (parallel branch 1)
    syntax_valid: Optional[bool]
    syntax_details: Optional[str]

    # Populated by check_deps (parallel branch 2)
    imports_found: Optional[list]
    risky_imports: Optional[list]

    # Populated by check_style (parallel branch 3)
    style_issues: Optional[list]

    # Populated by gather_results
    all_defects: Optional[list]
    all_warnings: Optional[list]
    all_ok: Optional[list]

    # Final output
    report: Optional[str]


# ─── Graph Builder ───
# We create a function that takes an initialized MCPClient and returns
# a compiled LangGraph. This keeps the client lifecycle outside the graph.
def create_review_graph(mcp: MCPClient):
    """
    Args:
        mcp: An active MCPClient connected to the code-review MCP server.
    """

    # ════════════════════════════════════════════════════════════
    #  NODE 1: Read the file from disk via MCP
    # ════════════════════════════════════════════════════════════
    async def read_file(state: ReviewState) -> dict:
        """Calls the MCP read_source_file tool.

        MCP handles: file I/O, error handling, path resolution.
        The agent doesn't need 'import open' — it just says 'tool, do this'.
        """
        print(f"  📂 [read_file] Reading {state['file_path']}...")
        result = await mcp.call_tool("read_source_file", {
            "path": state["file_path"]
        })

        if result.startswith("ERROR:"):
            print(f"     ❌ Failed: {result}")
            return {"content": None, "read_error": result}
        else:
            print(f"     ✅ Loaded {len(result)} characters")
            return {"content": result, "read_error": None}

    # ════════════════════════════════════════════════════════════
    #  NODE 2a: Syntax analysis (parallel branch)
    # ════════════════════════════════════════════════════════════
    async def analyze_syntax(state: ReviewState) -> dict:
        """Calls MCP analyze_syntax tool to parse the code with AST."""
        print(f"  🔍 [analyze_syntax] Parsing AST...")
        result = await mcp.call_tool("analyze_syntax", {
            "code": state["content"]
        })

        # The MCP server returns JSON as a string — parse it back
        import json
        data = json.loads(result)
        print(f"     Valid syntax: {data.get('valid_syntax')}, "
              f"Functions: {len(data.get('functions', []))}, "
              f"Classes: {len(data.get('classes', []))}")
        if data.get("warnings"):
            for w in data["warnings"]:
                print(f"     ⚠️  {w}")

        return {
            "syntax_valid": data.get("valid_syntax"),
            "syntax_details": result
        }

    # ════════════════════════════════════════════════════════════
    #  NODE 2b: Dependency check (parallel branch)
    # ════════════════════════════════════════════════════════════
    async def check_deps(state: ReviewState) -> dict:
        """Calls MCP check_dependencies to scan imports."""
        print(f"  📦 [check_deps] Scanning imports...")
        result = await mcp.call_tool("check_dependencies", {
            "code": state["content"]
        })

        import json
        data = json.loads(result)
        print(f"     Found {data.get('total_count', 0)} imports")
        for finding in data.get("risky_findings", []):
            print(f"     ⚠️  {finding}")

        return {
            "imports_found": data.get("imports", []),
            "risky_imports": data.get("risky_findings", [])
        }

    # ════════════════════════════════════════════════════════════
    #  NODE 2c: Code style check (parallel branch)
    # ════════════════════════════════════════════════════════════
    async def check_style(state: ReviewState) -> dict:
        """Calls MCP check_code_style for PEP8-style checks."""
        print(f"  ✨ [check_style] Running style checks...")
        result = await mcp.call_tool("check_code_style", {
            "code": state["content"]
        })

        import json
        data = json.loads(result)
        print(f"     Found {data.get('issue_count', 0)} style issues")
        for issue in data.get("issues", [])[:3]:  # Show first 3
            print(f"     ⚠️  {issue}")
        if data.get("issue_count", 0) > 3:
            print(f"     ... and {data['issue_count'] - 3} more")

        return {
            "style_issues": data.get("issues", [])
        }

    # ════════════════════════════════════════════════════════════
    #  NODE 3: Gather results from all parallel branches
    # ════════════════════════════════════════════════════════════
    async def gather_results(state: ReviewState) -> dict:
        """Collect outputs from all three parallel analyzers and
        categorize findings into defects, warnings, and passed checks.

        This node runs AFTER all three parallel branches complete
        (LangGraph fan-in). It has access to ALL their outputs.
        """
        print(f"  🔗 [gather_results] Joining parallel results...")

        defects = []
        warnings = []
        ok_checks = []

        # --- Syntax results ---
        if state.get("syntax_valid") is True:
            ok_checks.append("Python syntax is valid (AST parsed successfully)")
            # Add syntax warnings as warnings
            import json
            details = json.loads(state.get("syntax_details", "{}"))
            for w in details.get("warnings", []):
                warnings.append(w)
        elif state.get("syntax_valid") is False:
            defects.append("Python syntax error — file cannot be parsed")

        # --- Import/Dependency results ---
        risky = state.get("risky_imports", [])
        if risky:
            for r in risky:
                defects.append(f"Risky dependency: {r}")
        else:
            ok_checks.append("No risky dependencies detected")

        if state.get("imports_found"):
            ok_checks.append(
                f"Dependencies scanned: {len(state['imports_found'])} imports found"
            )

        # --- Style results ---
        style_issues = state.get("style_issues", [])
        if style_issues:
            for s in style_issues:
                warnings.append(f"Style: {s}")
        else:
            ok_checks.append("No style issues found")

        print(f"     → {len(defects)} defects, {len(warnings)} warnings, "
              f"{len(ok_checks)} passed checks")
        return {
            "all_defects": defects,
            "all_warnings": warnings,
            "all_ok": ok_checks
        }

    # ════════════════════════════════════════════════════════════
    #  NODE 4: Generate the final report via MCP
    # ════════════════════════════════════════════════════════════
    async def generate_report(state: ReviewState) -> dict:
        """Calls the MCP format_report tool to produce a markdown report.

        All the heavy lifting (formatting, markdown generation) is done
        by the MCP server, not by the agent. The agent just passes data.
        """
        print(f"  📝 [generate_report] Building report...")
        result = await mcp.call_tool("format_report", {
            "defects": state.get("all_defects", []),
            "warnings": state.get("all_warnings", []),
            "ok_checks": state.get("all_ok", []),
            "file_name": state["file_path"].split("/")[-1]
        })
        print(f"     ✅ Report generated ({len(result)} chars)")
        return {"report": result}

    # ════════════════════════════════════════════════════════════
    #  ROUTER: Fan-out to parallel analyzers
    # ════════════════════════════════════════════════════════════
    def route_to_analyzers(state: ReviewState):
        """After reading the file, launch all three analyzers in PARALLEL.

        This uses LangGraph's Send() — it creates multiple concurrent
        paths through the graph. Each Send() says "run node X with this state".

        The three nodes run simultaneously because they're independent.
        """
        if state.get("read_error"):
            # File couldn't be read — end the workflow
            return [Send("generate_report", state)]

        return [
            Send("analyze_syntax", state),
            Send("check_deps", state),
            Send("check_style", state),
        ]

    # ════════════════════════════════════════════════════════════
    #  BUILD THE GRAPH
    # ════════════════════════════════════════════════════════════
    builder = StateGraph(ReviewState)

    # Register all nodes
    builder.add_node("read_file", read_file)
    builder.add_node("analyze_syntax", analyze_syntax)
    builder.add_node("check_deps", check_deps)
    builder.add_node("check_style", check_style)
    builder.add_node("gather_results", gather_results)
    builder.add_node("generate_report", generate_report)

    # START → read_file
    builder.add_edge(START, "read_file")

    # read_file → (analyze_syntax, check_deps, check_style) in parallel
    # route_to_analyzers returns Send() objects that fan out
    builder.add_conditional_edges("read_file", route_to_analyzers, [
        "analyze_syntax", "check_deps", "check_style"
    ])

    # All three analyzers → gather_results (this is the FAN-IN / JOIN)
    # LangGraph waits for ALL three to complete before running gather_results
    builder.add_edge(["analyze_syntax", "check_deps", "check_style"], "gather_results")

    # gather_results → generate_report
    builder.add_edge("gather_results", "generate_report")

    # generate_report → END
    builder.add_edge("generate_report", END)

    # Compile the graph into a runnable object
    graph = builder.compile()

    # Print the graph structure (useful for debugging)
    print("   ╔══ LangGraph Structure ═══════════════════════╗")
    try:
        # Modern LangGraph exposes the graph via get_graph()
        for node_name, metadata in graph.nodes.items():
            print(f"   ║  {node_name}")
    except Exception:
        pass
    print("   ╚═══════════════════════════════════════════════╝")

    return graph
