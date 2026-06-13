"""
S0RA CLI — Interactive chat interface.
Mirrors Hermes cli.py but simplified for Sora.
"""

import os
import sys
from pathlib import Path

# Load config and env early
from sora_cli.config import load_config, load_sora_dotenv, get_env_value
from sora_constants import ensure_sora_home as ensure_hermes_home, get_sora_home
from sora_logging import setup_logging

load_sora_dotenv()
setup_logging("cli")
ensure_hermes_home()


def main(args) -> int:
    """Start interactive chat session."""
    config = load_config()

    # Check if TUI mode requested
    use_tui = os.environ.get("SORA_TUI") == "1"
    if use_tui:
        return _run_tui(config, args)

    # Classic REPL
    return _run_repl(config, args)


def _run_repl(config: dict, args) -> int:
    """Run the classic REPL interface."""
    from sora_cli.colors import color, Colors
    from sora_cli.cli_output import print_info, print_success, print_warning

    print()
    print(color("═══ S0RA Agent ═══", Colors.CYAN, Colors.BOLD))
    print(color("Your voice-first AI companion with Gemini Live, Vapi & MCP", Colors.DIM))
    print()

    # Show tool availability
    gemini_key = get_env_value("GEMINI_API_KEY") or get_env_value("GOOGLE_API_KEY")
    vapi_key = get_env_value("VAPI_API_KEY")
    discord_token = get_env_value("DISCORD_BOT_TOKEN")

    tools = []
    if gemini_key and discord_token:
        tools.append("voice-live (Gemini Live)")
    if vapi_key and discord_token:
        tools.append("voice-vapi (Vapi.ai)")
    if config.get("mcp", {}).get("servers"):
        tools.append(f"MCP ({len(config['mcp']['servers'])} servers)")

    if tools:
        print_success(f"Available: {', '.join(tools)}")
    else:
        print_warning("Run 'sora setup' to configure voice bridges and MCP")

    print()
    print_info("Type your message, or use commands:")
    print_info("  /voice live   - Start Gemini Live bridge")
    print_info("  /voice vapi   - Start Vapi bridge")
    print_info("  /voice leave  - Stop voice bridge")
    print_info("  /mcp start    - Start MCP server")
    print_info("  /help         - Show all commands")
    print_info("  /quit         - Exit")
    print()

    # Simple REPL loop
    try:
        while True:
            try:
                user_input = input(color("▸ ", Colors.CYAN, Colors.BOLD)).strip()
            except (KeyboardInterrupt, EOFError):
                print()
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                _handle_command(user_input[1:], config)
            else:
                # In a real implementation, this would call the agent
                print_info("Agent not yet connected — this is a CLI skeleton")
                print_info("Run 'sora voice live' or 'sora voice vapi' to start a voice bridge")
                print_info("Or 'sora mcp start' to start the MCP server")

    except KeyboardInterrupt:
        pass

    print()
    print_success("Goodbye!")
    return 0


def _handle_command(cmd: str, config: dict) -> None:
    """Handle slash commands in REPL."""
    from sora_cli.cli_output import print_info, print_success, print_error

    parts = cmd.split()
    command = parts[0].lower()
    args = parts[1:]

    if command in ("help", "h"):
        print("Available commands:")
        print("  /voice live [guild] [channel]  - Start Gemini Live bridge")
        print("  /voice vapi [guild] [channel]  - Start Vapi bridge")
        print("  /voice status                  - Show voice bridge status")
        print("  /voice leave [guild]           - Stop voice bridge")
        print("  /mcp start [port] [transport]  - Start MCP server")
        print("  /mcp status                    - Show MCP status")
        print("  /mcp stop                      - Stop MCP server")
        print("  /setup                         - Run setup wizard")
        print("  /config <show|get|set>         - Config management")
        print("  /status                        - Show system status")
        print("  /quit, /exit                   - Exit SORA")

    elif command == "voice":
        if len(args) == 0:
            print_error("Usage: /voice <live|vapi|status|leave>")
        else:
            sub = args[0]
            if sub == "live":
                print_info("Use: sora voice live --guild <id> --channel <id>")
            elif sub == "vapi":
                print_info("Use: sora voice vapi --guild <id> --channel <id>")
            elif sub == "status":
                print_info("Use: sora voice status")
            elif sub == "leave":
                print_info("Use: sora voice leave --guild <id>")
            else:
                print_error(f"Unknown voice command: {sub}")

    elif command == "mcp":
        if len(args) == 0:
            print_error("Usage: /mcp <start|status|stop>")
        else:
            sub = args[0]
            if sub == "start":
                print_info("Use: sora mcp start --port 3000 --transport stdio")
            elif sub == "status":
                print_info("Use: sora mcp status")
            elif sub == "stop":
                print_info("Use: sora mcp stop")
            else:
                print_error(f"Unknown mcp command: {sub}")

    elif command == "setup":
        print_info("Run: sora setup")

    elif command == "config":
        print_info("Run: sora config <show|get|set|reset|edit|wizard>")

    elif command == "status":
        print_info("Run: sora status")

    elif command in ("quit", "exit", "q"):
        print_success("Goodbye!")
        sys.exit(0)

    else:
        print_error(f"Unknown command: /{command}. Type /help for help.")


def _run_tui(config: dict, args) -> int:
    """Run the TUI (Ink/React) interface."""
    from sora_cli.cli_output import print_info

    print_info("TUI mode not yet implemented")
    print_info("Falling back to classic REPL...")
    return _run_repl(config, args)