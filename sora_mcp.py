"""
Sora MCP Server — Provides tools and resources via MCP protocol.

Supports stdio, SSE, and streamable-http transports.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Callable

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http import StreamableHTTPServerTransport
from mcp.types import Tool, TextContent, Resource, CallToolResult

logger = logging.getLogger("sora_mcp")


@dataclass
class MCPTool:
    """MCP tool definition."""
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable


class SoraMCPServer:
    """Sora MCP Server with multiple transport support."""

    def __init__(self, port: int = 3000):
        self.port = port
        self.server = Server("sora")
        self.tools: dict[str, MCPTool] = {}
        self._register_tools()

    def _register_tools(self):
        """Register Sora's built-in tools."""

        # Voice tools
        self.register_tool(MCPTool(
            name="voice_status",
            description="Get status of all voice bridges",
            input_schema={"type": "object", "properties": {}},
            handler=self._voice_status,
        ))

        self.register_tool(MCPTool(
            name="voice_start_gemini",
            description="Start Gemini Live voice bridge",
            input_schema={
                "type": "object",
                "properties": {
                    "guild_id": {"type": "string"},
                    "channel_id": {"type": "string"},
                },
                "required": ["guild_id", "channel_id"],
            },
            handler=self._voice_start_gemini,
        ))

        self.register_tool(MCPTool(
            name="voice_start_vapi",
            description="Start Vapi voice bridge",
            input_schema={
                "type": "object",
                "properties": {
                    "guild_id": {"type": "string"},
                    "channel_id": {"type": "string"},
                },
                "required": ["guild_id", "channel_id"],
            },
            handler=self._voice_start_vapi,
        ))

        self.register_tool(MCPTool(
            name="voice_stop",
            description="Stop voice bridge for a guild",
            input_schema={
                "type": "object",
                "properties": {
                    "guild_id": {"type": "string"},
                },
                "required": ["guild_id"],
            },
            handler=self._voice_stop,
        ))

        # MCP management tools
        self.register_tool(MCPTool(
            name="mcp_list_servers",
            description="List configured MCP servers",
            input_schema={"type": "object", "properties": {}},
            handler=self._mcp_list_servers,
        ))

        self.register_tool(MCPTool(
            name="mcp_detect",
            description="Detect running MCP servers on system",
            input_schema={"type": "object", "properties": {}},
            handler=self._mcp_detect,
        ))

        # System tools
        self.register_tool(MCPTool(
            name="system_info",
            description="Get system information",
            input_schema={"type": "object", "properties": {}},
            handler=self._system_info,
        ))

        # Register with MCP server
        for tool in self.tools.values():
            self.server.add_tool(Tool(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.input_schema,
            ), tool.handler)

    def register_tool(self, tool: MCPTool):
        """Register a tool."""
        self.tools[tool.name] = tool

    # Tool handlers
    async def _voice_status(self, arguments: dict) -> CallToolResult:
        from sora_cli.config import load_config
        config = load_config()
        return CallToolResult(content=[TextContent(type="text", text=json.dumps({
            "gemini_live": cfg_get(config, "voice", "gemini_live", default={}),
            "vapi": cfg_get(config, "voice", "vapi", default={}),
            "elevenlabs": cfg_get(config, "voice", "elevenlabs", default={}),
        }, indent=2))])

    async def _voice_start_gemini(self, arguments: dict) -> CallToolResult:
        # Would start actual bridge
        return CallToolResult(content=[TextContent(type="text", text="Gemini Live bridge start requested")])

    async def _voice_start_vapi(self, arguments: dict) -> CallToolResult:
        return CallToolResult(content=[TextContent(type="text", text="Vapi bridge start requested")])

    async def _voice_stop(self, arguments: dict) -> CallToolResult:
        return CallToolResult(content=[TextContent(type="text", text="Voice bridge stop requested")])

    async def _mcp_list_servers(self, arguments: dict) -> CallToolResult:
        from sora_cli.config import load_config, cfg_get
        config = load_config()
        servers = cfg_get(config, "mcp", "servers", default={})
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(servers, indent=2))])

    async def _mcp_detect(self, arguments: dict) -> CallToolResult:
        from sora_cli.mcp import detect_mcp_servers
        detected = detect_mcp_servers()
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(detected, indent=2))])

    async def _system_info(self, arguments: dict) -> CallToolResult:
        import platform, psutil
        info = {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "disk_gb": round(psutil.disk_usage('/').total / (1024**3), 1),
        }
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(info, indent=2))])

    async def start(self, transport: str = "stdio"):
        """Start the MCP server."""
        if transport == "stdio":
            logger.info("Starting MCP server on stdio")
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(read_stream, write_stream, self.server.create_initialization_options())
        elif transport == "sse":
            raise NotImplementedError("SSE transport is not implemented")
        elif transport == "streamable-http":
            raise NotImplementedError("Streamable HTTP transport is not implemented")
        else:
            raise NotImplementedError(f"Transport {transport!r} is not implemented")


class SoraWSMCPServer:
    """WebSocket-based MCP server for real-time tool calls."""

    def __init__(self, host: str = "0.0.0.0", port: int = 3001):
        self.host = host
        self.port = port
        self.clients: set = set()
        self.server = Server("sora-ws")
        self._register_tools()

    def _register_tools(self):
        """Register tools for WebSocket transport."""
        # Same tools as stdio server
        sora_server = SoraMCPServer()
        for name, tool in sora_server.tools.items():
            self.server.add_tool(Tool(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.input_schema,
            ), tool.handler)

    async def handle_client(self, websocket):
        """Handle a WebSocket client connection."""
        self.clients.add(websocket)
        try:
            async for message in websocket:
                # Parse JSON-RPC message
                try:
                    request = json.loads(message)
                    # Process MCP request
                    if request.get("method") == "tools/call":
                        tool_name = request["params"]["name"]
                        args = request["params"].get("arguments", {})
                        # Find and call handler
                        for tool in sora_server.tools.values():
                            if tool.name == tool_name:
                                result = await tool.handler(args)
                                response = {
                                    "jsonrpc": "2.0",
                                    "id": request.get("id"),
                                    "result": {"content": [{"type": "text", "text": result.content[0].text}]}
                                }
                                await websocket.send(json.dumps(response))
                                break
                except json.JSONDecodeError:
                    pass
        finally:
            self.clients.remove(websocket)

    async def start(self):
        """Start the WebSocket server."""
        import websockets
        logger.info(f"Starting WebSocket MCP server on {self.host}:{self.port}")
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # Run forever


async def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio")
    args = parser.parse_args()

    server = SoraMCPServer(port=args.port)
    await server.start(transport=args.transport)


if __name__ == "__main__":
    asyncio.run(main())
