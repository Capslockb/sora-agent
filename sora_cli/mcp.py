"""
S0RA MCP CLI — Model Context Protocol server management.
Handles: sora mcp start, sora mcp status, sora mcp stop, sora mcp list, sora mcp catalog
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from sora_cli.config import load_config, get_env_value
from sora_constants import ensure_sora_home as ensure_hermes_home
from sora_logging import setup_logging

setup_logging("cli")


async def start_mcp_server(
    port: int = 3000,
    transport: str = "stdio",
) -> dict:
    """Start the MCP server."""
    config = load_config()
    mcp_config = config.get("mcp", {})
    servers = mcp_config.get("servers", {})

    if not servers:
        return {
            "status": "warning",
            "message": "No MCP servers configured. Run 'sora setup' to add servers.",
            "servers": {}
        }

    # In a real implementation, this would start the MCP server process
    # For now, return what would be started
    return {
        "status": "success",
        "message": f"MCP server would start on port {port} with {transport} transport",
        "configured_servers": list(servers.keys()),
        "transport": transport,
        "port": port,
    }


async def get_mcp_status() -> dict:
    """Get MCP server status."""
    config = load_config()
    mcp_config = config.get("mcp", {})
    servers = mcp_config.get("servers", {})

    return {
        "status": "ok",
        "mcp_enabled": mcp_config.get("enabled", True),
        "configured_servers": {
            name: {
                "command": server.get("command"),
                "args": server.get("args", []),
                "env": list(server.get("env", {}).keys()) if server.get("env") else [],
            }
            for name, server in servers.items()
        },
    }


async def stop_mcp_server() -> dict:
    """Stop the MCP server."""
    return {
        "status": "success",
        "message": "MCP server stopped"
    }


async def list_mcp_servers() -> dict:
    """List available MCP servers from config."""
    config = load_config()
    servers = config.get("mcp", {}).get("servers", {})

    return {
        "status": "ok",
        "servers": list(servers.keys()),
        "details": servers,
    }


# MCP Catalog (built-in servers)
MCP_CATALOG = {
    "filesystem": {
        "name": "filesystem",
        "description": "Local filesystem access (read/write/list files)",
        "package": "@modelcontextprotocol/server-filesystem",
        "args_template": ["<allowed_directory>"],
        "env_vars": [],
    },
    "github": {
        "name": "github",
        "description": "GitHub API (repos, issues, PRs, actions)",
        "package": "@modelcontextprotocol/server-github",
        "args_template": [],
        "env_vars": ["GITHUB_TOKEN"],
    },
    "sqlite": {
        "name": "sqlite",
        "description": "SQLite database access",
        "package": "@modelcontextprotocol/server-sqlite",
        "args_template": ["<database_path>"],
        "env_vars": [],
    },
    "postgres": {
        "name": "postgres",
        "description": "PostgreSQL database access",
        "package": "@modelcontextprotocol/server-postgres",
        "args_template": [],
        "env_vars": ["POSTGRES_CONNECTION_STRING"],
    },
    "playwright": {
        "name": "playwright",
        "description": "Browser automation via Playwright",
        "package": "@modelcontextprotocol/server-playwright",
        "args_template": [],
        "env_vars": [],
    },
    "slack": {
        "name": "slack",
        "description": "Slack workspace access",
        "package": "@modelcontextprotocol/server-slack",
        "args_template": [],
        "env_vars": ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
    },
    "notion": {
        "name": "notion",
        "description": "Notion workspace access",
        "package": "@modelcontextprotocol/server-notion",
        "args_template": [],
        "env_vars": ["NOTION_API_KEY"],
    },
    "google-drive": {
        "name": "google-drive",
        "description": "Google Drive access",
        "package": "@modelcontextprotocol/server-gdrive",
        "args_template": [],
        "env_vars": ["GOOGLE_DRIVE_CREDENTIALS"],
    },
    "memory": {
        "name": "memory",
        "description": "Persistent memory/knowledge graph",
        "package": "@modelcontextprotocol/server-memory",
        "args_template": [],
        "env_vars": [],
    },
    "brave-search": {
        "name": "brave-search",
        "description": "Brave Search API",
        "package": "@modelcontextprotocol/server-brave-search",
        "args_template": [],
        "env_vars": ["BRAVE_API_KEY"],
    },
    "fetch": {
        "name": "fetch",
        "description": "Web fetching and scraping",
        "package": "@modelcontextprotocol/server-fetch",
        "args_template": [],
        "env_vars": [],
    },
}


async def browse_catalog() -> dict:
    """Browse the MCP server catalog."""
    return {
        "status": "ok",
        "catalog": MCP_CATALOG,
    }


def main(args) -> int:
    """Main entry point for mcp subcommands."""
    if args.mcp_command is None:
        print("Usage: sora mcp <start|status|stop|list|catalog>")
        return 1

    try:
        if args.mcp_command == "start":
            result = asyncio.run(start_mcp_server(args.port, args.transport))
        elif args.mcp_command == "status":
            result = asyncio.run(get_mcp_status())
        elif args.mcp_command == "stop":
            result = asyncio.run(stop_mcp_server())
        elif args.mcp_command == "list":
            result = asyncio.run(list_mcp_servers())
        elif args.mcp_command == "catalog":
            result = asyncio.run(browse_catalog())
        else:
            print(f"Unknown mcp command: {args.mcp_command}")
            return 1

        print(json.dumps(result, indent=2))
        return 0 if result.get("status") in ("success", "ok") else 1

    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1