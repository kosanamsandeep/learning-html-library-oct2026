"""
╔══════════════════════════════════════════════════════════════════╗
║  MCP SERVER: Code Review Tools                                  ║
║                                                                ║
║  This is an MCP (Model Context Protocol) server that exposes    ║
║  code-review capabilities as tools. ANY agent that speaks MCP   ║
║  — Claude Code, LangGraph, Copilot, Codex — can discover and    ║
║  call these tools. That's the whole point of MCP.               ║
║                                                                ║
║  Run:  python server/mcp_server.py                              ║
║  (It runs over stdio, so a parent process spawns it)            ║
╚══════════════════════════════════════════════════════════════════╝
"""
import ast
import json
import re
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ─── Create the MCP server instance ───
# The server name identifies it to clients during initialization
app = Server("code-review-tools")


# ─── Tool 1: Read a source file ───
# Every MCP tool has: name, description, and inputSchema (JSON Schema)
# The description is critical — the AI agent reads it to decide when to call this tool
@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="read_source_file",
            description="Read a Python source file from disk. Returns raw file content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative path to the file"
                    }
                },
                "required": ["path"]
            }
        ),
        # ─── Tool 2: Check Python syntax via AST ───
        Tool(
            name="analyze_syntax",
            description="Check Python code for syntax errors using AST parsing. "
                        "Returns valid_syntax, function/class names, and warnings like bare except clauses.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python source code to analyze"
                    }
                },
                "required": ["code"]
            }
        ),
        # ─── Tool 3: Check for risky imports ───
        Tool(
            name="check_dependencies",
            description="Extract all import statements from Python code and flag "
                        "known risky or deprecated packages (pickle, eval, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python source code to scan for imports"
                    }
                },
                "required": ["code"]
            }
        ),
        # ─── Tool 4: PEP8-style checks ───
        Tool(
            name="check_code_style",
            description="Basic style checks: line length >100, trailing whitespace, "
                        "naming convention violations (function snake_case, class PascalCase).",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python source code to style-check"
                    }
                },
                "required": ["code"]
            }
        ),
        # ─── Tool 5: Format a report ───
        Tool(
            name="format_report",
            description="Format code review findings into structured markdown. "
                        "Takes defects (hard errors), warnings (soft issues), and passed checks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "defects": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of defects/failures found"
                    },
                    "warnings": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of warnings found"
                    },
                    "ok_checks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of checks that passed"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "Name of the reviewed file"
                    }
                },
                "required": ["defects", "warnings", "ok_checks", "file_name"]
            }
        ),
    ]


# ─── Tool Implementations ───
# MCP dispatches calls here by tool name. Each tool parses its own arguments
# from the `arguments` dict and returns TextContent with the result.
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    # ─── Tool 1: Read file ───
    if name == "read_source_file":
        path = arguments["path"]
        try:
            with open(path, "r") as f:
                content = f.read()
            return [TextContent(type="text", text=content)]
        except Exception as e:
            return [TextContent(type="text", text=f"ERROR: {str(e)}")]

    # ─── Tool 2: AST syntax analysis ───
    elif name == "analyze_syntax":
        code = arguments["code"]
        try:
            tree = ast.parse(code)
            # Walk the AST and collect structure info
            funcs = [
                n.name for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            classes = [
                n.name for n in ast.walk(tree)
                if isinstance(n, ast.ClassDef)
            ]
            # Flag bare except clauses — they catch ALL exceptions silently
            bare_excepts = len([
                n for n in ast.walk(tree)
                if isinstance(n, ast.ExceptHandler) and n.type is None
            ])
            result = {
                "valid_syntax": True,
                "functions": funcs,
                "classes": classes,
                "warnings": []
            }
            if bare_excepts > 0:
                result["warnings"].append(
                    f"Found {bare_excepts} bare 'except:' clause(s) — "
                    "catches ALL exceptions silently, hides bugs"
                )
            return [TextContent(type="text", text=json.dumps(result))]
        except SyntaxError as e:
            return [TextContent(type="text", text=json.dumps({
                "valid_syntax": False,
                "error": str(e),
                "lineno": e.lineno,
                "text": e.text
            }))]

    # ─── Tool 3: Dependency check ───
    elif name == "check_dependencies":
        code = arguments["code"]
        imports = set()
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)

        # Known risky packages — this is YOUR org's policy encoded as data
        # In a real setup this would come from a database or policy file
        risky_packages = {
            "pickle": "Unsafe deserialization — code execution risk with untrusted data",
            "os.system": "Use subprocess.run() instead — os.system is deprecated",
            "shutil": "Destructive operations — ensure rm/move calls are validated",
            "eval": "Code injection risk — never use with untrusted input",
            "exec": "Code injection risk — never use with untrusted input",
        }

        findings = []
        for imp in sorted(imports):
            base = imp.split(".")[0]
            if base in risky_packages:
                findings.append(f"`{imp}` – {risky_packages[base]}")

        return [TextContent(type="text", text=json.dumps({
            "imports": sorted(imports),
            "total_count": len(imports),
            "risky_findings": findings
        }))]

    # ─── Tool 4: Code style check ───
    elif name == "check_code_style":
        code = arguments["code"]
        issues = []
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                issues.append(f"Line {i}: {len(line)} chars exceeds 100 limit")
            if line != line.rstrip():
                issues.append(f"Line {i}: trailing whitespace")
            if re.match(r"^\s*def [A-Z]", line):
                issues.append(f"Line {i}: function '{line.strip()}' should be snake_case")
            if re.match(r"^\s*class [a-z]", line):
                issues.append(f"Line {i}: class '{line.strip()}' should be PascalCase")

        return [TextContent(type="text", text=json.dumps({
            "total_lines": len(lines),
            "issues": issues,
            "issue_count": len(issues)
        }))]

    # ─── Tool 5: Format the final report ───
    elif name == "format_report":
        args = arguments
        lines = []
        lines.append(f"# 📋 Code Review Report: `{args['file_name']}`")
        lines.append("")

        # Defects — things that MUST be fixed
        lines.append("## 🔴 Defects (Must Fix)")
        if args.get("defects"):
            for d in args["defects"]:
                lines.append(f"- ❌ {d}")
        else:
            lines.append("_No defects found_")
        lines.append("")

        # Warnings — things that SHOULD be fixed
        lines.append("## 🟡 Warnings (Should Fix)")
        if args.get("warnings"):
            for w in args["warnings"]:
                lines.append(f"- ⚠️ {w}")
        else:
            lines.append("_No warnings_")
        lines.append("")

        # Passed checks
        lines.append("## ✅ Passed Checks")
        if args.get("ok_checks"):
            for o in args["ok_checks"]:
                lines.append(f"- ✅ {o}")
        else:
            lines.append("_None_")
        lines.append("")

        # Summary
        n_defects = len(args.get("defects", []))
        n_warnings = len(args.get("warnings", []))
        n_ok = len(args.get("ok_checks", []))
        lines.append(f"**Summary:** {n_defects} defects, {n_warnings} warnings, "
                     f"{n_ok} checks passed")

        return [TextContent(type="text", text="\n".join(lines))]

    raise ValueError(f"Unknown tool: {name}")


# ─── Entry point ───
# The server runs over stdio — a parent process (our LangGraph agent) spawns
# this script and communicates via stdin/stdout using JSON-RPC messages.
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
