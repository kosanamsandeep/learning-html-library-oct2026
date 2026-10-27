"""
╔══════════════════════════════════════════════════════════════════╗
║  MCP CLIENT WRAPPER                                             ║
║                                                                ║
║  This wraps an MCP server connection so LangGraph nodes can     ║
║  call tools without dealing with MCP protocol details.          ║
║                                                                ║
║  Flow:                                                          ║
║    LangGraph Node → MCPClient.call_tool() → stdio JSON-RPC      ║
║                                              → MCP Server       ║
║                                              → tool runs        ║
║    LangGraph Node ← result string          ← response           ║
╚══════════════════════════════════════════════════════════════════╝
"""
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Manages a connection to an MCP server and exposes its tools.

    Usage:
        async with MCPClient("server/mcp_server.py") as client:
            tools = await client.list_tools()
            result = await client.call_tool("some_tool", {"arg": "val"})
    """

    def __init__(self, server_script: str):
        """
        Args:
            server_script: Path to the MCP server Python script.
                           The client spawns it as a subprocess over stdio.
        """
        self.server_params = StdioServerParameters(
            command="python",
            args=[server_script]
        )
        self.session: ClientSession | None = None
        self._client = None  # keep reference to stdio_client context manager

    async def __aenter__(self):
        """Start the MCP server subprocess and establish a session.

        The sequence is:
        1. Spawn `python server/mcp_server.py` as a subprocess
        2. Connect to its stdin/stdout with JSON-RPC
        3. Initialize the MCP session (handshake)
        4. Now tools are ready to call
        """
        # stdio_client returns (read_stream, write_stream) as an async context
        self._client = stdio_client(self.server_params)
        read, write = await self._client.__aenter__()

        # ClientSession wraps the streams with JSON-RPC messaging
        self.session = await ClientSession(read, write).__aenter__()
        await self.session.initialize()
        return self

    async def __aexit__(self, *args):
        """Clean shutdown: close the session, then the subprocess.

        Note: MCP SDK has a known issue where the cancel scope error fires
        when the session is closed from a different async task than it was
        created in (which happens with LangGraph's parallel Send()). We
        swallow that specific error since it's harmless.
        """
        real_errors = []
        if self.session:
            try:
                await self.session.__aexit__(*args)
            except Exception as e:
                real_errors.append(e)
        if self._client:
            try:
                await self._client.__aexit__(*args)
            except Exception as e:
                real_errors.append(e)
        # Swallow the cancel-scope cross-task error — it's a known MCP SDK
        # issue when the session is closed from a different async task
        # than it was created in (happens with LangGraph's parallel Send())
        for e in real_errors:
            msg = str(e)
            if "cancel scope" not in msg or "different task" not in msg:
                raise e

    async def list_tools(self):
        """Discover what tools the MCP server offers.

        Returns a list of Tool objects with name, description, inputSchema.
        In a real org, you'd cache this or load from a registry.
        """
        result = await self.session.list_tools()
        return result.tools

    async def call_tool(self, tool_name: str, arguments: dict = None) -> str:
        """Call an MCP tool and return its text result.

        Args:
            tool_name: The tool's 'name' field from list_tools()
            arguments: Dict matching the tool's inputSchema

        Returns:
            The text content of the tool's response
        """
        result = await self.session.call_tool(tool_name, arguments or {})
        # MCP tools return content blocks (text, images, embedded resources)
        if result.content and len(result.content) > 0:
            # For our demo, all tools return TextContent
            return result.content[0].text
        return json.dumps({"error": "No content returned"})
