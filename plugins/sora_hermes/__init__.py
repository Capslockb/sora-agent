"""
S0RA Hermes Plugin — Allows Sora to work as a Hermes plugin.

This plugin registers Sora's voice bridge tools and MCP integration
with the Hermes agent, so Hermes can use Sora's functionality.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("sora-hermes-plugin")


def register(ctx):
    """Register Sora tools and commands with Hermes."""
    
    # Register voice bridge tools
    ctx.register_tool(
        name="sora_voice_live",
        toolset="sora",
        schema={
            "name": "sora_voice_live",
            "description": "Start a Sora Gemini Live voice bridge in a Discord voice channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "guild_id": {"type": "string", "description": "Discord guild ID"},
                    "channel_id": {"type": "string", "description": "Voice channel ID to join"},
                    "user_id": {"type": "string", "description": "Discord user ID whose current voice channel should be used when channel_id is omitted"},
                },
                "additionalProperties": False,
            },
        },
        handler=_sora_voice_live_handler,
        check_fn=lambda: True,
        is_async=True,
    )

    ctx.register_tool(
        name="sora_voice_vapi",
        toolset="sora",
        schema={
            "name": "sora_voice_vapi",
            "description": "Start a Sora Vapi.ai voice bridge in a Discord voice channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "guild_id": {"type": "string", "description": "Discord guild ID"},
                    "channel_id": {"type": "string", "description": "Voice channel ID to join"},
                    "user_id": {"type": "string", "description": "Discord user ID whose current voice channel should be used when channel_id is omitted"},
                },
                "additionalProperties": False,
            },
        },
        handler=_sora_voice_vapi_handler,
        check_fn=lambda: True,
        is_async=True,
    )

    ctx.register_tool(
        name="sora_voice_leave",
        toolset="sora",
        schema={
            "name": "sora_voice_leave",
            "description": "Stop a Sora voice bridge for a guild.",
            "parameters": {
                "type": "object",
                "properties": {
                    "guild_id": {"type": "string", "description": "Discord guild ID"},
                },
                "required": ["guild_id"],
                "additionalProperties": False,
            },
        },
        handler=_sora_voice_leave_handler,
        check_fn=lambda: True,
        is_async=True,
    )

    ctx.register_tool(
        name="sora_voice_status",
        toolset="sora",
        schema={
            "name": "sora_voice_status",
            "description": "Check the Sora voice bridge health and metrics.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        handler=_sora_voice_status_handler,
        check_fn=lambda: True,
        is_async=True,
    )

    # Register MCP tools
    ctx.register_tool(
        name="sora_mcp_start",
        toolset="sora",
        schema={
            "name": "sora_mcp_start",
            "description": "Start the Sora MCP server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "port": {"type": "integer", "description": "MCP server port", "default": 3000},
                    "transport": {"type": "string", "enum": ["stdio", "sse", "streamable-http"], "default": "stdio"},
                },
                "additionalProperties": False,
            },
        },
        handler=_sora_mcp_start_handler,
        check_fn=lambda: True,
        is_async=True,
    )

    ctx.register_tool(
        name="sora_mcp_status",
        toolset="sora",
        schema={
            "name": "sora_mcp_status",
            "description": "Get the Sora MCP server status.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        handler=_sora_mcp_status_handler,
        check_fn=lambda: True,
        is_async=True,
    )

    # Register slash commands for Discord
    async def _slash_sora_voice_live(raw_args: str) -> str:
        return "Use /voice-live from the discord-voice plugin for Gemini Live, or /voice-vapi from discord-vapi plugin."

    async def _slash_sora_voice_vapi(raw_args: str) -> str:
        return "Use /voice-vapi from the discord-vapi plugin for Vapi voice."

    ctx.register_command(
        name="sora-voice-live",
        handler=_slash_sora_voice_live,
        description="Start Sora Gemini Live voice bridge (use discord-voice plugin instead)",
        args_hint="",
    )

    ctx.register_command(
        name="sora-voice-vapi",
        handler=_slash_sora_voice_vapi,
        description="Start Sora Vapi voice bridge (use discord-vapi plugin instead)",
        args_hint="",
    )


# Tool handlers (these call out to the sora CLI or direct implementation)
def _run_cli(cmd: list[str]) -> str:
    import subprocess

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Command failed with exit code {result.returncode}")
    return result.stdout.strip()


async def _sora_voice_live_handler(args: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
    try:
        import sys

        cmd = [sys.executable, "-m", "sora_cli.main", "voice", "live"]
        for flag, key in (("--guild", "guild_id"), ("--channel", "channel_id"), ("--user", "user_id")):
            value = args.get(key) if args else None
            if value:
                cmd.extend([flag, value])
        return _run_cli(cmd)
    except Exception as e:
        return {"error": str(e)}


async def _sora_voice_vapi_handler(args: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
    try:
        import sys

        cmd = [sys.executable, "-m", "sora_cli.main", "voice", "vapi"]
        for flag, key in (("--guild", "guild_id"), ("--channel", "channel_id"), ("--user", "user_id")):
            value = args.get(key) if args else None
            if value:
                cmd.extend([flag, value])
        return _run_cli(cmd)
    except Exception as e:
        return {"error": str(e)}


async def _sora_voice_leave_handler(args: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
    try:
        import sys

        guild_id = args.get("guild_id") if args else None
        if not guild_id:
            raise ValueError("guild_id is required")
        return _run_cli(
            [sys.executable, "-m", "sora_cli.main", "voice", "leave", "--guild", guild_id]
        )
    except Exception as e:
        return {"error": str(e)}


async def _sora_voice_status_handler(args: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
    try:
        import sys

        return _run_cli([sys.executable, "-m", "sora_cli.main", "voice", "status"])
    except Exception as e:
        return {"error": str(e)}


async def _sora_mcp_start_handler(args: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
    try:
        import sys

        port = args.get("port", 3000) if args else 3000
        transport = args.get("transport", "stdio") if args else "stdio"
        return _run_cli(
            [
                sys.executable,
                "-m",
                "sora_cli.main",
                "mcp",
                "start",
                "--port",
                str(port),
                "--transport",
                transport,
            ]
        )
    except Exception as e:
        return {"error": str(e)}


async def _sora_mcp_status_handler(args: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
    try:
        import sys

        return _run_cli([sys.executable, "-m", "sora_cli.main", "mcp", "status"])
    except Exception as e:
        return {"error": str(e)}
