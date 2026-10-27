#!/usr/bin/env python3
"""
test_client.py — Test the MCP servers without needing Claude Code.

This script uses the MCP Python SDK to connect to a running server
and exercise its tools programmatically.

Usage:
    # In terminal 1 — start the docs server:
    python server.py

    # In terminal 2 — run this test:
    python test_client.py

    # Or test the examples server:
    # In terminal 1: python examples_server.py
    # Then here:     python test_client.py --server examples_server.py
"""

from __future__ import annotations
import sys
import json
import argparse
import asyncio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_server(server_script: str) -> None:
    """Connect to an MCP server via stdio and test all its tools."""
    server_path = Path(server_script).resolve()
    if not server_path.exists():
        print(f"❌ Server script not found: {server_path}")
        return

    print(f"\n{'='*60}")
    print(f"🧩 Connecting to MCP server: {server_path.name}")
    print(f"{'='*60}")

    # Create server parameters for stdio connection
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            print(f"✅ Connected! Protocol: MCP")

            # List available tools
            tools_result = await session.list_tools()
            tools = tools_result.tools
            print(f"\n📋 Available tools ({len(tools)}):")
            for t in tools:
                print(f"   • {t.name}: {t.description[:80]}...")

            # ── Test each tool ──────────────────────────────────
            for tool in tools:
                print(f"\n{'─'*50}")
                print(f"🔧 Testing: {tool.name}")
                print(f"{'─'*50}")

                try:
                    # Determine test arguments based on tool name and schema
                    test_args = _get_test_args(tool.name, tool.inputSchema)
                    if test_args is None:
                        print(f"   ⏭️  Skipped (no test args defined)")
                        continue

                    result = await session.call_tool(tool.name, test_args)
                    content = result.content[0].text if result.content else "(no content)"
                    # Show first 800 chars
                    preview = content[:800]
                    if len(content) > 800:
                        preview += "\n   ... (truncated)"
                    print(f"\n{preview}")

                except Exception as e:
                    print(f"   ❌ Error: {e}")

    print(f"\n{'='*60}")
    print(f"✅ All tests completed for {server_path.name}")
    print(f"{'='*60}\n")


def _get_test_args(name: str, schema: dict) -> dict | None:
    """Generate test arguments for a given tool based on its schema."""
    if name == "search_docs":
        return {"query": "fastapi cors", "top_k": 3}
    elif name == "list_topics":
        return {}
    elif name == "get_topic":
        return {"title": "FastAPI — CORS Middleware"}
    elif name == "calculator":
        return {"expression": "sqrt(144) * 2 + 10"}
    elif name == "current_time":
        return {"format": "readable"}
    elif name == "get_weather":
        return {"city": "Tokyo", "units": "celsius"}
    elif name == "text_stats":
        return {
            "text": "MCP (Model Context Protocol) is an open standard for "
                    "connecting AI agents to tools and data. It was announced "
                    "by Anthropic in late 2024. Think of it as USB-C for AI. "
                    "One server works with any compatible agent."
        }
    elif name == "unit_convert":
        return {"value": 100, "from_unit": "km", "to_unit": "mi"}
    elif name == "review_code":
        return {
            "input_data": {
                "code": (
                    "def process_data(data):\n"
                    "    try:\n"
                    "        result = data['key']\n"
                    "        return result\n"
                    "    except:\n"
                    "        pass\n"
                    "\n"
                    "password = 'supersecret123'\n"
                    "api_key = 'sk-abc123def456'\n"
                    "\n"
                    "def fetch_users():\n"
                    "    # This function has no docstring\n"
                    "    return []\n"
                ),
                "language": "python",
                "severity": "info",
            }
        }
    return None


def main():
    parser = argparse.ArgumentParser(description="Test MCP Servers")
    parser.add_argument(
        "--server",
        default="server.py",
        help="Path to the MCP server script to test (default: server.py)",
    )
    args = parser.parse_args()
    asyncio.run(test_server(args.server))


if __name__ == "__main__":
    main()
