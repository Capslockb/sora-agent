#!/usr/bin/env python3
"""
S0RA Agent CLI - Main entry point.

Usage:
    sora                     # Show voice-first help
    sora chat                # Hermes-compatible chat shell
    sora setup               # Interactive setup wizard
    sora voice               # Voice bridge management
    sora voice live          # Start Gemini Live voice bridge (Discord)
    sora voice vapi          # Start Vapi voice bridge (Discord)
    sora voice elevenlabs    # Start ElevenLabs voice bridge (Discord)
    sora voice status        # Show voice bridge status
    sora voice leave         # Stop voice bridge
    sora voice sip           # Manage SIP registration (Asterisk)
    sora voice ari           # Manage ARI connection (Asterisk)
    sora voice call          # Place outbound call via Asterisk
    sora voice hangup        # Hang up active call(s)
    sora voice voip-status   # Show VOIP bridge status (ARI, SIP, calls, Dograh)
    sora voice voip-config   # Manage VOIP configuration
    sora voice providers     # Manage voice providers (TTS/STT/LLM Voice)
    sora mcp                 # MCP server management
    sora mcp start           # Start MCP server
    sora mcp status          # Show MCP status
    sora status              # Show status of all components
    sora cron                # Manage cron jobs
    sora doctor              # Check configuration and dependencies
    sora logs                # View logs
    sora config              # Configuration management
    sora plugins             # Plugin management
    sora skills              # Skill management
    sora version             # Show version
    sora update              # Update to latest version
    sora uninstall           # Uninstall SORA Agent
    sora acp                 # Run as ACP server for editor integration
    sora tui                 # Launch Terminal UI (Ink/React)
"""

# IMPORTANT: sora_bootstrap must be the very first import — UTF-8 stdio on Windows
try:
    import sora_bootstrap  # noqa: F401
except ModuleNotFoundError:
    pass

import os
import sys


def _set_process_title() -> None:
    """Set the process title to 'sora' for ps/top/htop."""
    try:
        import setproctitle
        setproctitle.setproctitle("sora")
        return
    except ImportError:
        pass

    import ctypes
    import platform

    try:
        system = platform.system()
        if system == "Linux":
            libc = ctypes.CDLL("libc.so.6", use_errno=True)
            libc.prctl(15, b"sora", 0, 0, 0)
        elif system == "Darwin":
            libc = ctypes.CDLL("libc.dylib", use_errno=True)
            libc.pthread_setname_np(b"sora")
    except Exception:
        pass


# Early TUI detection (before heavy imports)
_EARLY_INTERFACE_CACHE: list | None = None


def _config_default_interface_early() -> str:
    """Read display.interface from config.yaml early."""
    global _EARLY_INTERFACE_CACHE
    if _EARLY_INTERFACE_CACHE is not None:
        return _EARLY_INTERFACE_CACHE[0]

    value = "cli"
    try:
        home = os.environ.get("SORA_HOME")
        if home:
            cfg_path = os.path.join(home, "config.yaml")
        else:
            from sora_constants import get_default_sora_root
            cfg_path = str(get_default_sora_root() / "config.yaml")

        if os.path.exists(cfg_path):
            import yaml
            with open(cfg_path, encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            disp = raw.get("display", {})
            if isinstance(disp, dict):
                iface = disp.get("interface")
                if isinstance(iface, str) and iface.strip().lower() == "tui":
                    value = "tui"
    except Exception:
        value = "cli"

    _EARLY_INTERFACE_CACHE = [value]
    return value


def _wants_tui_early(argv: list[str] | None = None) -> bool:
    """Early TUI decision."""
    if argv is None:
        argv = sys.argv[1:]
    if "--cli" in argv:
        return False
    if os.environ.get("SORA_TUI") == "1" or "--tui" in argv:
        return True
    return _config_default_interface_early() == "tui"


def _suppress_mouse_residue_early() -> None:
    """Suppress mouse tracking residue on TUI startup."""
    if os.environ.get("SORA_TUI_NO_EARLY_DISABLE") == "1":
        return
    if not _wants_tui_early():
        return
    try:
        if not os.isatty(1):
            return
        os.write(
            1,
            b"\x1b[?1003l\x1b[?1002l\x1b[?1001l\x1b[?1000l\x1b[?9l"
            b"\x1b[?1006l\x1b[?1005l\x1b[?1015l\x1b[?1016l\x1b[?2029l",
        )
    except OSError:
        pass


_suppress_mouse_residue_early()


def _print_fast_version_info() -> None:
    from sora_cli import __version__, __release_date__

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    print(f"S0RA Agent v{__version__} ({__release_date__})")
    print(f"Project: {project_root}")
    print(f"Python: {sys.version.split()[0]}")


def _try_termux_ultrafast_version() -> bool:
    """Handle `sora --version` before imports on Termux."""
    if os.environ.get("SORA_TERMUX_DISABLE_FAST_CLI") == "1":
        return False

    # Termux detection
    prefix = os.environ.get("PREFIX", "")
    is_termux = bool(
        os.environ.get("TERMUX_VERSION")
        or "com.termux/files/usr" in prefix
        or prefix.startswith("/data/data/com.termux/")
    )

    if not is_termux:
        return False

    if sys.argv[1:] not in (["--version"], ["-V"], ["version"]):
        return False

    _print_fast_version_info()
    return True


if _try_termux_ultrafast_version():
    raise SystemExit(0)

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional
import asyncio

# Subcommand builders — imported lazily in build_parser()
# from sora_cli.subcommands.* import build_*_parser


def _require_tty(command_name: str) -> None:
    """Exit if stdin is not a terminal (for interactive commands)."""
    if not sys.stdin.isatty():
        print(
            f"Error: 'sora {command_name}' requires an interactive terminal.\n"
            f"It cannot be run through a pipe or non-interactive subprocess.\n"
            f"Run it directly in your terminal instead.",
            file=sys.stderr,
        )
        sys.exit(1)


# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Profile override — MUST happen before any sora module import.
# ---------------------------------------------------------------------------
def _apply_profile_override() -> None:
    """Pre-parse --profile/-p and set SORA_HOME before module imports."""
    argv = sys.argv[1:]
    profile_name = None
    consume = 0

    for i, arg in enumerate(argv):
        if arg in {"--profile", "-p"} and i + 1 < len(argv):
            profile_name = argv[i + 1]
            consume = 2
            break
        elif arg.startswith("--profile="):
            profile_name = arg.split("=", 1)[1]
            consume = 1
            break

    # Validate profile name
    if profile_name is not None and consume == 2:
        import re
        if not re.match(r"^[a-z0-9][a-z0-9_-]{0,63}$", profile_name):
            profile_name = None
            consume = 0

    # If SORA_HOME already set and points to a profile, trust it
    sora_home_env = os.environ.get("SORA_HOME", "")
    if profile_name is None and sora_home_env:
        if Path(sora_home_env).parent.name == "profiles":
            return

    # Check active_profile in sora root
    if profile_name is None:
        try:
            from sora_constants import get_default_sora_root

            active_path = get_default_sora_root() / "active_profile"
            if active_path.exists():
                name = active_path.read_text().strip()
                if name and name != "default":
                    profile_name = name
                    consume = 0
        except (UnicodeDecodeError, OSError):
            pass

    # Apply profile
    if profile_name is not None:
        try:
            from sora_constants import resolve_profile_env

            sora_home = resolve_profile_env(profile_name)
        except (ValueError, FileNotFoundError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        except Exception as exc:
            print(
                f"Warning: profile override failed ({exc}), using default",
                file=sys.stderr,
            )
            return

        os.environ["SORA_HOME"] = sora_home

        if consume > 0:
            for i, arg in enumerate(argv):
                if arg in {"--profile", "-p"}:
                    start = i + 1
                    sys.argv = sys.argv[:start] + sys.argv[start + consume :]
                    break
                elif arg.startswith("--profile="):
                    start = i + 1
                    sys.argv = sys.argv[:start] + sys.argv[start + 1 :]
                    break


_apply_profile_override()


# Load .env early
from sora_cli.config import load_sora_dotenv

load_sora_dotenv(project_env=PROJECT_ROOT / ".env")


# Security redact from config.yaml -> env var BEFORE logging init
_FORCE_IPV4_EARLY = False
try:
    import yaml

    cfg_path = Path(os.environ.get("SORA_HOME", str(Path.home() / ".sora"))) / "config.yaml"
    if cfg_path.exists():
        with open(cfg_path, encoding="utf-8") as f:
            early_cfg = yaml.safe_load(f) or {}

        if "SORA_REDACT_SECRETS" not in os.environ:
            sec_cfg = early_cfg.get("security", {})
            if isinstance(sec_cfg, dict):
                redact = sec_cfg.get("redact_secrets")
                if redact is not None:
                    os.environ["SORA_REDACT_SECRETS"] = str(redact).lower()

        net_cfg = early_cfg.get("network", {})
        if isinstance(net_cfg, dict) and net_cfg.get("force_ipv4"):
            _FORCE_IPV4_EARLY = True
except Exception:
    pass


# Initialize logging
try:
    from sora_logging import setup_logging as _setup_logging

    _setup_logging(
        mode=(
            "gui"
            if next((arg for arg in sys.argv[1:] if not arg.startswith("-")), "")
            in {"dashboard", "gui", "desktop"}
            else "cli"
        )
    )
except Exception:
    pass

if _FORCE_IPV4_EARLY:
    try:
        from sora_constants import apply_ipv4_preference as _apply_ipv4

        _apply_ipv4(force=True)
    except Exception:
        pass

import logging
import threading
import time as _time
from datetime import datetime

from sora_cli import __version__, __release_date__

# Build the main parser
parser = argparse.ArgumentParser(
    prog="sora",
    description="S0RA Agent — Hermes companion CLI for voice bridges, VOIP, and MCP",
    add_help=False,
)


# Global flags
parser.add_argument(
    "-h", "--help", action="help", help="Show this help message and exit"
)
parser.add_argument(
    "-V", "--version", action="store_true", help="Show version and exit"
)
parser.add_argument(
    "--profile", "-p", metavar="NAME", help="Use a specific SORA profile"
)
parser.add_argument(
    "--tui", action="store_true", help="Use TUI interface (Ink/React)"
)
parser.add_argument(
    "--cli", action="store_true", help="Force classic CLI (overrides --tui/config)"
)
parser.add_argument(
    "--quiet", "-q", action="store_true", help="Suppress non-error output"
)

subparsers = parser.add_subparsers(dest="command", metavar="<command>")


# ---- Helper to add subcommand parsers ----
def _add_subcommand(name: str, help_text: str, aliases: list = None):
    sub = subparsers.add_parser(name, help=help_text, add_help=False)
    sub.add_argument("-h", "--help", action="help", help="Show help for this command")
    if aliases:
        for alias in aliases:
            # Create alias parser without parents to avoid -h/--help conflict
            alias_parser = subparsers.add_parser(alias, help=argparse.SUPPRESS, add_help=False)
            alias_parser.add_argument("-h", "--help", action="help", help=argparse.SUPPRESS)
            # Copy the subparser's actions (but we'll handle dispatch manually in main())
    return sub


# ---- chat ----
chat_parser = _add_subcommand("chat", "Hermes-compatible chat shell", ["c"])
chat_parser.add_argument("--toolsets", help="Comma-separated toolsets to enable")
chat_parser.add_argument("--skills", help="Comma-separated skills to load")
chat_parser.add_argument("--model", help="Model to use for this session")
chat_parser.add_argument("--provider", help="Provider to use")
chat_parser.add_argument("--no-memory", action="store_true", help="Disable memory")


# ---- setup ----
setup_parser = _add_subcommand("setup", "Run interactive setup wizard")
setup_parser.add_argument(
    "--non-interactive", action="store_true", help="Print guidance for headless setup"
)


# ---- voice ----
voice_parser = _add_subcommand("voice", "Voice bridge management")
voice_sub = voice_parser.add_subparsers(dest="voice_command", metavar="<subcommand>")

voice_live_parser = voice_sub.add_parser("live", help="Start Gemini Live voice bridge", add_help=False)
voice_live_parser.add_argument("-h", "--help", action="help")
voice_live_parser.add_argument("--guild", help="Discord guild ID")
voice_live_parser.add_argument("--channel", help="Discord voice channel ID")
voice_live_parser.add_argument("--user", help="Discord user ID (to infer channel)")

voice_vapi_parser = voice_sub.add_parser("vapi", help="Start Vapi voice bridge", add_help=False)
voice_vapi_parser.add_argument("-h", "--help", action="help")
voice_vapi_parser.add_argument("--guild", help="Discord guild ID")
voice_vapi_parser.add_argument("--channel", help="Discord voice channel ID")
voice_vapi_parser.add_argument("--user", help="Discord user ID (to infer channel)")

voice_elevenlabs_parser = voice_sub.add_parser("elevenlabs", help="Start ElevenLabs Conversational AI voice bridge", add_help=False)
voice_elevenlabs_parser.add_argument("-h", "--help", action="help")
voice_elevenlabs_parser.add_argument("--guild", help="Discord guild ID")
voice_elevenlabs_parser.add_argument("--channel", help="Discord voice channel ID")
voice_elevenlabs_parser.add_argument("--user", help="Discord user ID (to infer channel)")

voice_status_parser = voice_sub.add_parser("status", help="Show voice bridge status", add_help=False)
voice_status_parser.add_argument("-h", "--help", action="help")

voice_leave_parser = voice_sub.add_parser("leave", help="Stop voice bridge", add_help=False)
voice_leave_parser.add_argument("-h", "--help", action="help")
voice_leave_parser.add_argument("--guild", help="Discord guild ID (omit to stop all)")

# VOIP subcommands
# voice sip
sip_parser = voice_sub.add_parser("sip", help="Manage SIP registration", add_help=False)
sip_parser.add_argument("-h", "--help", action="help")
sip_sub = sip_parser.add_subparsers(dest="sip_action", metavar="<action>")
sip_register = sip_sub.add_parser("register", help="Register SIP endpoint", add_help=False)
sip_register.add_argument("-h", "--help", action="help")
sip_register.add_argument("--username", help="SIP username")
sip_register.add_argument("--password", help="SIP password")
sip_register.add_argument("--domain", help="SIP domain")
sip_unregister = sip_sub.add_parser("unregister", help="Unregister SIP endpoint", add_help=False)
sip_unregister.add_argument("-h", "--help", action="help")
sip_unregister.add_argument("--username", help="SIP username")
sip_unregister.add_argument("--password", help="SIP password")
sip_unregister.add_argument("--domain", help="SIP domain")
sip_status = sip_sub.add_parser("status", help="Show SIP registration status", add_help=False)
sip_status.add_argument("-h", "--help", action="help")

# voice ari
ari_parser = voice_sub.add_parser("ari", help="Manage ARI connection", add_help=False)
ari_parser.add_argument("-h", "--help", action="help")
ari_sub = ari_parser.add_subparsers(dest="ari_action", metavar="<action>")
ari_connect = ari_sub.add_parser("connect", help="Connect ARI application", add_help=False)
ari_connect.add_argument("-h", "--help", action="help")
ari_connect.add_argument("--app", help="ARI application name")
ari_disconnect = ari_sub.add_parser("disconnect", help="Disconnect ARI application", add_help=False)
ari_disconnect.add_argument("-h", "--help", action="help")
ari_disconnect.add_argument("--app", help="ARI application name")
ari_status = ari_sub.add_parser("status", help="Show ARI connection status", add_help=False)
ari_status.add_argument("-h", "--help", action="help")
ari_apps = ari_sub.add_parser("apps", help="List registered ARI applications", add_help=False)
ari_apps.add_argument("-h", "--help", action="help")

# voice call
call_parser = voice_sub.add_parser("call", help="Place an outbound call via Asterisk", add_help=False)
call_parser.add_argument("-h", "--help", action="help")
call_parser.add_argument("number", help="Phone number to call")
call_parser.add_argument("--caller-id", help="Caller ID to present")
call_parser.add_argument("--auto-answer", action="store_true", help="Auto-answer the call")
call_parser.add_argument("--record", action="store_true", help="Record the call")

# voice hangup
hangup_parser = voice_sub.add_parser("hangup", help="Hang up active call(s)", add_help=False)
hangup_parser.add_argument("-h", "--help", action="help")
hangup_parser.add_argument("--channel", help="Channel ID to hang up")
hangup_parser.add_argument("--all", action="store_true", help="Hang up all calls")

# voice voip-status
voip_status_parser = voice_sub.add_parser("voip-status", help="Show VOIP bridge status (ARI, SIP, calls, Dograh)", add_help=False)
voip_status_parser.add_argument("-h", "--help", action="help")

# voice voip-config
voip_config_parser = voice_sub.add_parser("voip-config", help="Manage VOIP configuration", add_help=False)
voip_config_parser.add_argument("-h", "--help", action="help")
voip_config_sub = voip_config_parser.add_subparsers(dest="voip_config_action", metavar="<action>")
voip_config_show = voip_config_sub.add_parser("show", help="Show current VOIP configuration", add_help=False)
voip_config_show.add_argument("-h", "--help", action="help")
voip_config_set = voip_config_sub.add_parser("set", help="Set a VOIP config value", add_help=False)
voip_config_set.add_argument("-h", "--help", action="help")
voip_config_set.add_argument("key", help="Config key (e.g., asterisk_ari_url, dograh_ws_url)")
voip_config_set.add_argument("value", help="Config value")
voip_config_reload = voip_config_sub.add_parser("reload", help="Reload VOIP configuration in plugin", add_help=False)
voip_config_reload.add_argument("-h", "--help", action="help")

# voice providers
providers_parser = voice_sub.add_parser("providers", help="Manage voice providers (TTS/STT/LLM Voice)", add_help=False)
providers_sub = providers_parser.add_subparsers(dest="providers_command", metavar="<subcommand>")

providers_list_parser = providers_sub.add_parser("list", help="List available providers", add_help=False)
providers_list_parser.add_argument("-h", "--help", action="help")

providers_enable_parser = providers_sub.add_parser("enable", help="Enable a provider", add_help=False)
providers_enable_parser.add_argument("-h", "--help", action="help")
providers_enable_parser.add_argument("provider", help="Provider name (gemini-live, vapi, elevenlabs, edge-tts, openai-tts, whisper)")

providers_disable_parser = providers_sub.add_parser("disable", help="Disable a provider", add_help=False)
providers_disable_parser.add_argument("-h", "--help", action="help")
providers_disable_parser.add_argument("provider", help="Provider name")

providers_config_parser = providers_sub.add_parser("config", help="Configure a provider", add_help=False)
providers_config_parser.add_argument("-h", "--help", action="help")
providers_config_parser.add_argument("provider", help="Provider name")

# ---- mcp ----
mcp_parser = _add_subcommand("mcp", "MCP server management")
mcp_sub = mcp_parser.add_subparsers(dest="mcp_command", metavar="<subcommand>")

mcp_start_parser = mcp_sub.add_parser("start", help="Start MCP server", add_help=False)
mcp_start_parser.add_argument("-h", "--help", action="help")
mcp_start_parser.add_argument("--port", type=int, default=3000, help="MCP server port")
mcp_start_parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio")

mcp_status_parser = mcp_sub.add_parser("status", help="Show MCP status", add_help=False)
mcp_status_parser.add_argument("-h", "--help", action="help")

mcp_stop_parser = mcp_sub.add_parser("stop", help="Stop MCP server", add_help=False)
mcp_stop_parser.add_argument("-h", "--help", action="help")

mcp_list_parser = mcp_sub.add_parser("list", help="List available MCP servers", add_help=False)
mcp_list_parser.add_argument("-h", "--help", action="help")

mcp_catalog_parser = mcp_sub.add_parser("catalog", help="Browse MCP server catalog", add_help=False)
mcp_catalog_parser.add_argument("-h", "--help", action="help")

mcp_ws_parser = mcp_sub.add_parser("ws", help="WebSocket MCP management", add_help=False)
mcp_ws_sub = mcp_ws_parser.add_subparsers(dest="mcp_ws_command", metavar="<subcommand>")

mcp_ws_start_parser = mcp_ws_sub.add_parser("start", help="Start WebSocket MCP server", add_help=False)
mcp_ws_start_parser.add_argument("-h", "--help", action="help")
mcp_ws_start_parser.add_argument("--port", type=int, default=3001, help="WebSocket port")
mcp_ws_start_parser.add_argument("--host", default="0.0.0.0", help="Bind host")

mcp_ws_stop_parser = mcp_ws_sub.add_parser("stop", help="Stop WebSocket MCP server", add_help=False)
mcp_ws_stop_parser.add_argument("-h", "--help", action="help")

mcp_ws_status_parser = mcp_ws_sub.add_parser("status", help="Show WebSocket MCP status", add_help=False)
mcp_ws_status_parser.add_argument("-h", "--help", action="help")

mcp_ws_list_parser = mcp_ws_sub.add_parser("list", help="List connected WebSocket clients", add_help=False)
mcp_ws_list_parser.add_argument("-h", "--help", action="help")



# ---- status ----
status_parser = _add_subcommand("status", "Show status of all components")
status_parser.add_argument("--json", action="store_true", help="Output as JSON")

# ---- cron ----
cron_parser = _add_subcommand("cron", "Manage scheduled tasks")
cron_sub = cron_parser.add_subparsers(dest="cron_command", metavar="<subcommand>")

for sub_name, sub_help in [
    ("list", "List cron jobs"),
    ("add", "Add a new cron job"),
    ("create", "Create a new cron job (interactive)"),
    ("edit", "Edit a cron job"),
    ("pause", "Pause a cron job"),
    ("resume", "Resume a cron job"),
    ("run", "Run a cron job now"),
    ("remove", "Remove a cron job"),
    ("status", "Check if cron scheduler is running"),
]:
    sub = cron_sub.add_parser(sub_name, help=sub_help, add_help=False)
    sub.add_argument("-h", "--help", action="help")


# ---- doctor ----
doctor_parser = _add_subcommand("doctor", "Check configuration and dependencies")
doctor_parser.add_argument("--fix", action="store_true", help="Attempt to fix issues")


# ---- benchmark ----
benchmark_parser = _add_subcommand("benchmark", "Run performance benchmarks")
benchmark_parser.add_argument("--json", action="store_true", help="Output as JSON")
benchmark_parser.add_argument("--quick", action="store_true", help="Run quick subset")


# ---- logs ----
logs_parser = _add_subcommand("logs", "View logs")
logs_parser.add_argument("--follow", "-f", action="store_true", help="Follow log output")
logs_parser.add_argument("--level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
logs_parser.add_argument("--session", help="Filter by session ID")
logs_parser.add_argument("--lines", "-n", type=int, default=100, help="Number of lines to show")


# ---- config ----
config_parser = _add_subcommand("config", "Configuration management")
config_sub = config_parser.add_subparsers(dest="config_command", metavar="<subcommand>")

for sub_name, sub_help in [
    ("show", "Show current configuration"),
    ("set", "Set a configuration value"),
    ("get", "Get a configuration value"),
    ("reset", "Reset configuration to defaults"),
    ("wizard", "Re-run setup wizard"),
    ("edit", "Open config.yaml in editor"),
]:
    sub = config_sub.add_parser(sub_name, help=sub_help, add_help=False)
    sub.add_argument("-h", "--help", action="help")
    if sub_name == "set":
        sub.add_argument("key", help="Config key (dot notation)")
        sub.add_argument("value", help="Value to set")


# ---- plugins ----
plugins_parser = _add_subcommand("plugins", "Plugin management")
plugins_sub = plugins_parser.add_subparsers(dest="plugins_command", metavar="<subcommand>")

# plugins list
list_parser = plugins_sub.add_parser("list", help="List installed plugins", add_help=False)
list_parser.add_argument("-h", "--help", action="help")

# plugins enable
enable_parser = plugins_sub.add_parser("enable", help="Enable a plugin", add_help=False)
enable_parser.add_argument("-h", "--help", action="help")
enable_parser.add_argument("plugin_name", help="Plugin name to enable")

# plugins disable
disable_parser = plugins_sub.add_parser("disable", help="Disable a plugin", add_help=False)
disable_parser.add_argument("-h", "--help", action="help")
disable_parser.add_argument("plugin_name", help="Plugin name to disable")

# plugins install
install_parser = plugins_sub.add_parser("install", help="Install a plugin from GitHub", add_help=False)
install_parser.add_argument("-h", "--help", action="help")
install_parser.add_argument("plugin_name", help="GitHub repo (user/repo)")

# plugins remove
remove_parser = plugins_sub.add_parser("remove", help="Remove a plugin", add_help=False)
remove_parser.add_argument("-h", "--help", action="help")
remove_parser.add_argument("plugin_name", help="Plugin name to remove")

# plugins update
update_parser = plugins_sub.add_parser("update", help="Update all plugins", add_help=False)
update_parser.add_argument("-h", "--help", action="help")

# ---- dashboard ----
dashboard_parser = _add_subcommand("dashboard", "Launch web dashboard")
dashboard_sub = dashboard_parser.add_subparsers(dest="dashboard_command", metavar="<subcommand>")

dashboard_start_parser = dashboard_sub.add_parser("start", help="Start dashboard server", add_help=False)
dashboard_start_parser.add_argument("-h", "--help", action="help")
dashboard_start_parser.add_argument("--port", type=int, default=3000, help="Dashboard port")
dashboard_start_parser.add_argument("--host", default="0.0.0.0", help="Bind host")
dashboard_start_parser.add_argument("--api-port", type=int, default=8080, help="API server port")

dashboard_build_parser = dashboard_sub.add_parser("build", help="Build dashboard for production", add_help=False)
dashboard_build_parser.add_argument("-h", "--help", action="help")

dashboard_dev_parser = dashboard_sub.add_parser("dev", help="Start dashboard in dev mode", add_help=False)
dashboard_dev_parser.add_argument("-h", "--help", action="help")
dashboard_dev_parser.add_argument("--port", type=int, default=3000, help="Dev server port")


# ---- skills ----
# ---- providers (top-level) ----
providers_top_parser = _add_subcommand("providers", "Manage voice providers (TTS/STT/LLM Voice)")
providers_top_sub = providers_top_parser.add_subparsers(dest="providers_command", metavar="<subcommand>")

providers_top_list_parser = providers_top_sub.add_parser("list", help="List available providers", add_help=False)
providers_top_list_parser.add_argument("-h", "--help", action="help")

providers_top_enable_parser = providers_top_sub.add_parser("enable", help="Enable a provider", add_help=False)
providers_top_enable_parser.add_argument("-h", "--help", action="help")
providers_top_enable_parser.add_argument("provider", help="Provider name (gemini-live, vapi, elevenlabs, edge-tts, openai-tts, whisper)")

providers_top_disable_parser = providers_top_sub.add_parser("disable", help="Disable a provider", add_help=False)
providers_top_disable_parser.add_argument("-h", "--help", action="help")
providers_top_disable_parser.add_argument("category", choices=["llm_voice", "tts", "stt"], help="Category to reset")

providers_top_config_parser = providers_top_sub.add_parser("config", help="Configure a provider", add_help=False)
providers_top_config_parser.add_argument("-h", "--help", action="help")
providers_top_config_parser.add_argument("provider", help="Provider name")

providers_top_status_parser = providers_top_sub.add_parser("status", help="Show current provider status", add_help=False)
providers_top_status_parser.add_argument("-h", "--help", action="help")


# ---- skills ----
skills_parser = _add_subcommand("skills", "Skill management")
skills_sub = skills_parser.add_subparsers(dest="skills_command", metavar="<subcommand>")

for sub_name, sub_help in [
    ("search", "Search for skills"),
    ("browse", "Browse available skills"),
    ("inspect", "Inspect a skill"),
    ("install", "Install a skill"),
    ("audit", "Audit installed skills"),
    ("list", "List installed skills"),
    ("update", "Update all skills"),
]:
    sub = skills_sub.add_parser(sub_name, help=sub_help, add_help=False)
    sub.add_argument("-h", "--help", action="help")


# ---- version ----
version_parser = _add_subcommand("version", "Show version", ["v", "-V", "--version"])


# ---- update ----
update_parser = _add_subcommand("update", "Update SORA Agent to latest version")
update_parser.add_argument("--force", action="store_true", help="Force update even if up to date")
update_parser.add_argument("--check-only", action="store_true", help="Only check for updates")


# ---- voip ----
voip_parser = _add_subcommand("voip", "VOIP bridge management (Asterisk + Dograh + Gemini Live)")
voip_sub = voip_parser.add_subparsers(dest="voip_command", metavar="<subcommand>")

voip_start_parser = voip_sub.add_parser("start", help="Start VOIP bridge", add_help=False)
voip_start_parser.add_argument("-h", "--help", action="help")
voip_start_parser.add_argument("--config", "-c", help="Config file path")
voip_start_parser.add_argument("--dograh-ws", help="Dograh WebSocket URL")
voip_start_parser.add_argument("--gemini-model", help="Gemini model")
voip_start_parser.add_argument("--detach", action="store_true", help="Run in background")

voip_stop_parser = voip_sub.add_parser("stop", help="Stop VOIP bridge", add_help=False)
voip_stop_parser.add_argument("-h", "--help", action="help")

voip_status_parser = voip_sub.add_parser("status", help="Show VOIP bridge status", add_help=False)
voip_status_parser.add_argument("-h", "--help", action="help")
voip_status_parser.add_argument("--json", action="store_true", help="Output as JSON")

voip_calls_parser = voip_sub.add_parser("calls", help="List active VOIP calls", add_help=False)
voip_calls_parser.add_argument("-h", "--help", action="help")
voip_calls_parser.add_argument("--json", action="store_true", help="Output as JSON")

voip_hangup_parser = voip_sub.add_parser("hangup", help="Hang up a VOIP call", add_help=False)
voip_hangup_parser.add_argument("-h", "--help", action="help")
voip_hangup_parser.add_argument("call_id", help="Call ID to hang up")

voip_control_parser = voip_sub.add_parser("control", help="Control a VOIP call (mute/unmute)", add_help=False)
voip_control_parser.add_argument("-h", "--help", action="help")
voip_control_parser.add_argument("call_id", help="Call ID")
voip_control_parser.add_argument("action", choices=["mute", "unmute"], help="Action to perform")


# ---- uninstall ----
uninstall_parser = _add_subcommand("uninstall", "Uninstall SORA Agent")
uninstall_parser.add_argument("--confirm", action="store_true", help="Confirm uninstallation")


# ---- acp ----
acp_parser = _add_subcommand("acp", "Run as ACP server for editor integration")
acp_parser.add_argument("--port", type=int, default=0, help="Port for ACP server (0 = stdio)")


# ---- tui ----
tui_parser = _add_subcommand("tui", "Launch Terminal UI (Ink/React)")
tui_parser.add_argument("--build", action="store_true", help="Build TUI before launching")


def main() -> int:
    args = parser.parse_args()

    # Handle --version early
    if args.version or args.command == "version":
        _print_fast_version_info()
        return 0

    # Handle --cli flag overriding TUI
    if args.cli:
        os.environ["SORA_TUI"] = "0"

    # Handle --tui flag
    if args.tui:
        os.environ["SORA_TUI"] = "1"

    # Handle --quiet
    if args.quiet:
        os.environ["SORA_QUIET"] = "1"

    # Dispatch to subcommand handlers
    if args.command is None:
        parser.print_help()
        return 0

    handler_map = {
        "chat": _handle_chat,
        "c": _handle_chat,
        "setup": _handle_setup,
        "voice": _handle_voice,
        "mcp": _handle_mcp,
        "status": _handle_status,
        "cron": _handle_cron,
        "doctor": _handle_doctor,
        "benchmark": _handle_benchmark,
        "logs": _handle_logs,
        "config": _handle_config,
        "plugins": _handle_plugins,
        "skills": _handle_skills,
        "version": lambda _: (_print_fast_version_info(), 0)[1],
        "update": _handle_update,
        "uninstall": _handle_uninstall,
        "acp": _handle_acp,
        "tui": _handle_tui,
        "voip": _handle_voip,
        "providers": _handle_providers,
        "dashboard": _handle_dashboard,
    }

    handler = handler_map.get(args.command)
    if handler:
        try:
            return handler(args)
        except KeyboardInterrupt:
            print("\nInterrupted", file=sys.stderr)
            return 130
        except Exception as e:
            if args.quiet:
                return 1
            import traceback
            traceback.print_exc()
            return 1

    parser.print_help()
    return 1


# ---- Subcommand handlers (lazy import to keep startup fast) ----

def _handle_voip(args) -> int:
    from sora_cli.voip import main as voip_main
    return voip_main(args)


def _handle_chat(args) -> int:
    from sora_cli.cli import main as cli_main
    return cli_main(args)


def _handle_providers(args) -> int:
    from sora_cli.providers import main as providers_main
    return providers_main(args)


def _handle_setup(args) -> int:
    from sora_cli.setup import main as setup_main
    return setup_main(args)


def _handle_voice(args) -> int:
    from sora_cli.voice import main as voice_main
    return voice_main(args)


def _handle_mcp(args) -> int:
    from sora_cli.mcp import main as mcp_main
    return mcp_main(args)


def _handle_status(args) -> int:
    from sora_cli.status import main as status_main
    return status_main(args)


def _handle_cron(args) -> int:
    from sora_cli.cron import main as cron_main
    return cron_main(args)


def _handle_doctor(args) -> int:
    from sora_cli.doctor import main as doctor_main
    return doctor_main(args)


def _handle_logs(args) -> int:
    from sora_cli.logs import main as logs_main
    return logs_main(args)


def _handle_config(args) -> int:
    from sora_cli.config_cmd import main as config_main
    return config_main(args)


def _handle_plugins(args) -> int:
    from sora_cli.plugins import main as plugins_main
    return plugins_main(args)


def _handle_skills(args) -> int:
    from sora_cli.skills import main as skills_main
    return skills_main(args)


def _handle_update(args) -> int:
    from sora_cli.update import main as update_main
    return update_main(args)


def _handle_uninstall(args) -> int:
    from sora_cli.uninstall import main as uninstall_main
    return uninstall_main(args)


def _handle_acp(args) -> int:
    from acp_adapter.entry import main as acp_main
    return acp_main(args)


def _handle_benchmark(args) -> int:
    from sora_cli.benchmark import main as benchmark_main
    return benchmark_main(sys.argv[2:] if len(sys.argv) > 2 else [])


def _handle_tui(args) -> int:
    """Launch the TUI (Terminal UI)."""
    import subprocess
    import sys as _sys
    import importlib.util
    
    # Try to find the TUI in the installed package
    tui_path = None
    
    # Check if ui-tui package exists
    spec = importlib.util.find_spec("ui_tui")
    if spec and spec.origin:
        tui_path = Path(spec.origin).parent
    
    # Also try with hyphen
    if tui_path is None:
        spec = importlib.util.find_spec("ui-tui")
        if spec and spec.origin:
            tui_path = Path(spec.origin).parent
    
    # Fallback to PROJECT_ROOT for development
    if tui_path is None or not tui_path.exists():
        tui_path = PROJECT_ROOT / "ui-tui"
    
    if args.build:
        # Build the TUI
        print("Building S0RA TUI...")
        # Install npm dependencies first
        print("Installing npm dependencies...")
        result = subprocess.run(
            ["npm", "install"],
            cwd=tui_path,
            capture_output=False,
        )
        if result.returncode != 0:
            print("npm install failed", file=sys.stderr)
            return 1
        result = subprocess.run(
            ["npx", "esbuild", "src/cli.tsx", "--bundle", "--platform=node", "--outfile=dist/cli.js", "--external:ink", "--external:react", "--format=esm"],
            cwd=tui_path,
            capture_output=False,
        )
        if result.returncode != 0:
            print("Build failed", file=sys.stderr)
            return 1
        print("Build complete!")
    
    # Check if built
    cli_js = tui_path / "dist" / "cli.js"
    if not cli_js.exists():
        print("TUI not built. Run 'sora tui --build' first.", file=sys.stderr)
        return 1
    
    # Launch TUI
    print("Launching S0RA TUI...")
    try:
        subprocess.run(["node", str(cli_js)], cwd=tui_path)
    except Exception as e2:
        print(f"Failed to launch TUI: {e2}", file=sys.stderr)
        return 1
    return 0


def _handle_dashboard(args) -> int:
    """Handle dashboard commands."""
    subcommand = getattr(args, "dashboard_command", None)

    if subcommand is None:
        print("Sora Web Dashboard")
        print()
        print("Usage: sora dashboard <subcommand> [options]")
        print()
        print("Subcommands:")
        print("  start    Start dashboard server (production)")
        print("  dev      Start dashboard in development mode")
        print("  build    Build dashboard for production")
        print()
        return 0

    if subcommand == "build":
        import subprocess
        tui_path = PROJECT_ROOT / "website"
        print("Building dashboard...")
        result = subprocess.run(["npm", "install"], cwd=tui_path, capture_output=False)
        if result.returncode != 0:
            print("npm install failed", file=sys.stderr)
            return 1
        result = subprocess.run(["npm", "run", "build"], cwd=tui_path, capture_output=False)
        if result.returncode != 0:
            print("Build failed", file=sys.stderr)
            return 1
        print("Build complete!")
        return 0

    elif subcommand == "dev":
        import subprocess
        tui_path = PROJECT_ROOT / "website"
        port = args.port
        print(f"Starting dashboard dev server on port {port}...")
        try:
            subprocess.run(["npm", "run", "dev", "--", "--port", str(port)], cwd=tui_path)
        except KeyboardInterrupt:
            pass
        return 0

    elif subcommand == "start":
        import subprocess
        import threading
        import time
        import uvicorn
        from sora_api import app

        # Start API server in background
        api_config = uvicorn.Config(app, host=args.host, port=args.api_port, log_level="warning")
        api_server = uvicorn.Server(api_config)

        def run_api():
            asyncio.run(api_server.serve())

        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()

        # Wait a moment for API to start
        time.sleep(1)

        # Start dashboard preview server
        tui_path = PROJECT_ROOT / "website"
        dist_path = tui_path / "dist"
        if not dist_path.exists():
            print("Dashboard not built. Run 'sora dashboard build' first.")
            return 1

        print(f"Starting dashboard on http://{args.host}:{args.port}")
        print(f"API server on http://{args.host}:{args.api_port}")
        try:
            subprocess.run(["npx", "serve", "-s", "dist", "-l", str(args.port)], cwd=tui_path)
        except KeyboardInterrupt:
            pass
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())