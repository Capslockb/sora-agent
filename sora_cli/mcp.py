"""
Sora Agent — MCP Server Management CLI.

Handles stdio, SSE, and streamable-http MCP servers, plus WebSocket MCP.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

from sora_cli.config import load_config, save_config, cfg_get, cfg_set


class MCPManager:
    """Manages MCP servers."""

    def __init__(self):
        self.config = load_config()
        self.servers = cfg_get(self.config, "mcp", "servers", default={})
        self.ws_server = None
        self.ws_task = None

    def save(self):
        cfg_set(self.config, "mcp", "servers", self.servers)
        save_config(self.config)

    def list_servers(self) -> dict:
        """List configured MCP servers."""
        return self.servers

    def add_server(self, name: str, command: str, args: list = None, env: dict = None, transport: str = "stdio") -> None:
        """Add an MCP server configuration."""
        self.servers[name] = {
            "command": command,
            "args": args or [],
            "env": env or {},
            "transport": transport,
            "enabled": True,
        }
        self.save()

    def remove_server(self, name: str) -> bool:
        """Remove an MCP server configuration."""
        if name in self.servers:
            del self.servers[name]
            self.save()
            return True
        return False

    def toggle_server(self, name: str, enabled: bool) -> bool:
        """Enable/disable an MCP server."""
        if name in self.servers:
            self.servers[name]["enabled"] = enabled
            self.save()
            return True
        return False


async def start_mcp_server(port: int = 3000, transport: str = "stdio"):
    """Start the Sora MCP server."""
    from sora_mcp import SoraMCPServer

    server = SoraMCPServer(port=port)
    await server.start(transport=transport)


async def start_ws_mcp_server(host: str = "0.0.0.0", port: int = 3001):
    """Start the WebSocket MCP server."""
    from sora_mcp import SoraWSMCPServer

    server = SoraWSMCPServer(host=host, port=port)
    await server.start()


def detect_mcp_servers() -> list[dict]:
    """Detect MCP servers running on the system."""
    import psutil
    servers = []

    # Check common ports
    common_ports = [3000, 3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008, 3009, 3010]
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr.port in common_ports and conn.status == 'LISTEN':
            try:
                proc = psutil.Process(conn.pid)
                servers.append({
                    "port": conn.laddr.port,
                    "pid": conn.pid,
                    "process": proc.name(),
                    "cmdline": " ".join(proc.cmdline()[:3]),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                servers.append({"port": conn.laddr.port, "pid": conn.pid, "process": "unknown"})

    # Check for stdio MCP processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = " ".join(proc.info['cmdline'] or [])
            if 'mcp' in cmdline.lower() and ('stdio' in cmdline or 'mcp' in proc.info['name'].lower()):
                servers.append({
                    "type": "stdio",
                    "pid": proc.info['pid'],
                    "process": proc.info['name'],
                    "cmdline": cmdline[:100],
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return servers


def cmd_start(args) -> int:
    """Start MCP server."""
    from sora_cli.colors import Colors, color
    from sora_cli.cli_output import print_info, print_success
    from sora_cli.setup import print_header

    print_info(f"Starting MCP server on port {args.port} ({args.transport})")
    try:
        asyncio.run(start_mcp_server(args.port, args.transport))
        print_success("MCP server started")
        return 0
    except KeyboardInterrupt:
        print_info("Stopped")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_ws_start(args) -> int:
    """Start WebSocket MCP server."""
    from sora_cli.colors import Colors, color
    from sora_cli.cli_output import print_info, print_success
    from sora_cli.setup import print_header

    print_info(f"Starting WebSocket MCP server on {args.host}:{args.port}")
    try:
        asyncio.run(start_ws_mcp_server(args.host, args.port))
        print_success("WebSocket MCP server started")
        return 0
    except KeyboardInterrupt:
        print_info("Stopped")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_status(args) -> int:
    """Show MCP status."""
    from sora_cli.colors import Colors, color
    from sora_cli.cli_output import print_info, print_success
    from sora_cli.config import load_config
    from sora_cli.setup import print_header

    config = load_config()
    servers = cfg_get(config, "mcp", "servers", default={})

    print_header("MCP Servers")
    if servers:
        for name, info in servers.items():
            status = color("●", Colors.GREEN) if info.get("enabled") else color("○", Colors.RED)
            print(f"  {status} {name}: {info.get('command')} {' '.join(info.get('args', []))} ({info.get('transport', 'stdio')})")
    else:
        print_info("No MCP servers configured")

    print()
    print_header("Detected MCP Processes")
    detected = detect_mcp_servers()
    if detected:
        for s in detected:
            if s.get("type") == "stdio":
                print(f"  ● STDIO: {s['process']} (PID: {s['pid']}) - {s['cmdline']}")
            else:
                print(f"  ● Port {s['port']}: {s['process']} (PID: {s['pid']})")
    else:
        print_info("No MCP processes detected")

    return 0


def cmd_list(args) -> int:
    """List available MCP servers from catalog."""
    from sora_cli.colors import Colors, color
    from sora_cli.cli_output import print_info
    from sora_cli.setup import print_header

    # Built-in catalog
    catalog = [
        {"name": "filesystem", "description": "Local filesystem access", "package": "@modelcontextprotocol/server-filesystem"},
        {"name": "github", "description": "GitHub API integration", "package": "@modelcontextprotocol/server-github"},
        {"name": "sqlite", "description": "SQLite database access", "package": "@modelcontextprotocol/server-sqlite"},
        {"name": "postgres", "description": "PostgreSQL database access", "package": "@modelcontextprotocol/server-postgres"},
        {"name": "fetch", "description": "Web fetching", "package": "@modelcontextprotocol/server-fetch"},
        {"name": "brave-search", "description": "Brave search API", "package": "@modelcontextprotocol/server-brave-search"},
        {"name": "memory", "description": "Persistent memory", "package": "@modelcontextprotocol/server-memory"},
        {"name": "time", "description": "Time and timezone utilities", "package": "@modelcontextprotocol/server-time"},
        {"name": "everything", "description": "Test server with all features", "package": "@modelcontextprotocol/server-everything"},
    ]

    print_header("MCP Server Catalog")
    for s in catalog:
        print(f"  {color(s['name'], Colors.CYAN)}: {s['description']}")
        print(f"    Package: {s['package']}")
    print()
    print_info("Install with: npx -y <package>")
    print_info("Add to config: sora mcp add <name> --command npx --args \"-y,<package>\"")

    return 0


def cmd_add(args) -> int:
    """Add an MCP server."""
    from sora_cli.cli_output import print_success, print_error
    from sora_cli.colors import Colors, color

    manager = MCPManager()
    manager.add_server(args.name, args.command, args.args or [], args.env or {})
    print_success(f"Added MCP server: {args.name}")
    return 0


def cmd_remove(args) -> int:
    """Remove an MCP server."""
    from sora_cli.cli_output import print_success, print_error
    from sora_cli.colors import Colors, color

    manager = MCPManager()
    if manager.remove_server(args.name):
        print_success(f"Removed MCP server: {args.name}")
    else:
        print_error(f"Server not found: {args.name}")
        return 1
    return 0


def cmd_toggle(args) -> int:
    """Enable/disable an MCP server."""
    from sora_cli.cli_output import print_success, print_error
    from sora_cli.colors import Colors, color

    manager = MCPManager()
    if manager.toggle_server(args.name, args.enable):
        print_success(f"{'Enabled' if args.enable else 'Disabled'} MCP server: {args.name}")
    else:
        print_error(f"Server not found: {args.name}")
        return 1
    return 0


def cmd_catalog(args) -> int:
    """Browse MCP server catalog."""
    return cmd_list(args)


def main(args) -> int:
    """Main MCP command dispatcher."""
    subcommand = getattr(args, "mcp_command", None)

    if subcommand is None:
        print("MCP Server Management")
        print()
        print("Usage: sora mcp <subcommand> [options]")
        print()
        print("Subcommands:")
        print("  start       Start MCP server")
        print("  ws start    Start WebSocket MCP server")
        print("  status      Show MCP status and detected servers")
        print("  list        List available MCP servers from catalog")
        print("  catalog     Browse MCP server catalog")
        print("  add         Add an MCP server")
        print("  remove      Remove an MCP server")
        print("  enable      Enable an MCP server")
        print("  disable     Disable an MCP server")
        print()
        return 0

    # Handle ws subcommands
    if subcommand == "ws":
        ws_cmd = getattr(args, "mcp_ws_command", None)
        if ws_cmd == "start":
            return cmd_ws_start(args)
        elif ws_cmd == "stop":
            print("WebSocket MCP server stop not implemented yet")
            return 1
        elif ws_cmd == "status":
            print("WebSocket MCP status not implemented yet")
            return 1
        elif ws_cmd == "list":
            print("WebSocket client list not implemented yet")
            return 1
        else:
            print("Usage: sora mcp ws {start,stop,status,list}")
            return 1

    handlers = {
        "start": cmd_start,
        "status": cmd_status,
        "list": cmd_list,
        "catalog": cmd_catalog,
        "add": cmd_add,
        "remove": cmd_remove,
        "enable": lambda a: cmd_toggle(a) if setattr(a, 'enable', True) or True else None,
        "disable": lambda a: cmd_toggle(a) if setattr(a, 'enable', False) or True else None,
    }

    handler = handlers.get(subcommand)
    if handler:
        return handler(args)
    else:
        print(f"Unknown subcommand: {subcommand}")
        return 1


def build_parser(subparsers):
    """Add MCP subcommands to main parser."""
    mcp_parser = subparsers.add_parser("mcp", help="MCP server management")
    mcp_sub = mcp_parser.add_subparsers(dest="mcp_command", metavar="<subcommand>")

    # start
    start_p = mcp_sub.add_parser("start", help="Start MCP server")
    start_p.add_argument("-h", "--help", action="help")
    start_p.add_argument("--port", type=int, default=3000)
    start_p.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio")

    # ws
    ws_p = mcp_sub.add_parser("ws", help="WebSocket MCP management")
    ws_sub = ws_p.add_subparsers(dest="mcp_ws_command")
    ws_start = ws_sub.add_parser("start", help="Start WebSocket MCP server")
    ws_start.add_argument("-h", "--help", action="help")
    ws_start.add_argument("--host", default="0.0.0.0")
    ws_start.add_argument("--port", type=int, default=3001)
    ws_sub.add_parser("stop", help="Stop WebSocket MCP server").add_argument("-h", "--help", action="help")
    ws_sub.add_parser("status", help="WebSocket MCP status").add_argument("-h", "--help", action="help")
    ws_sub.add_parser("list", help="List WebSocket clients").add_argument("-h", "--help", action="help")

    # status
    mcp_sub.add_parser("status", help="Show MCP status").add_argument("-h", "--help", action="help")

    # list
    mcp_sub.add_parser("list", help="List MCP servers from catalog").add_argument("-h", "--help", action="help")

    # catalog
    mcp_sub.add_parser("catalog", help="Browse MCP server catalog").add_argument("-h", "--help", action="help")

    # add
    add_p = mcp_sub.add_parser("add", help="Add MCP server")
    add_p.add_argument("-h", "--help", action="help")
    add_p.add_argument("name")
    add_p.add_argument("--command", required=True)
    add_p.add_argument("--args", nargs="*")
    add_p.add_argument("--env", nargs="*", help="KEY=VAL pairs")

    # remove
    rem_p = mcp_sub.add_parser("remove", help="Remove MCP server")
    rem_p.add_argument("-h", "--help", action="help")
    rem_p.add_argument("name")

    # enable/disable
    en_p = mcp_sub.add_parser("enable", help="Enable MCP server")
    en_p.add_argument("-h", "--help", action="help")
    en_p.add_argument("name")
    dis_p = mcp_sub.add_parser("disable", help="Disable MCP server")
    dis_p.add_argument("-h", "--help", action="help")
    dis_p.add_argument("name")


# Import helpers
from sora_cli.setup import print_header, Colors, color
from sora_cli.cli_output import print_info, print_success, print_error