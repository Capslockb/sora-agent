"""
S0RA Status CLI — Show status of all components.
"""

import json
import os
import sys
from pathlib import Path

from sora_cli.config import load_config, get_env_value
from sora_constants import get_sora_home, get_config_path, get_env_path, get_logs_dir, get_state_db_path
from sora_logging import setup_logging

setup_logging("cli")


def check_command(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    import shutil
    return shutil.which(cmd) is not None


def get_service_status() -> dict:
    """Get status of system services."""
    status = {}

    # Check systemd services
    try:
        import subprocess
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "sora-gateway"],
            capture_output=True, text=True, timeout=5
        )
        status["gateway"] = result.stdout.strip() if result.returncode == 0 else "inactive"
    except Exception:
        status["gateway"] = "unknown"

    return status


def main(args) -> int:
    config = load_config()
    sora_home = get_sora_home()

    status = {
        "version": "0.1.0",
        "sora_home": str(sora_home),
        "config": {
            "exists": get_config_path().exists(),
            "path": str(get_config_path()),
        },
        "env": {
            "exists": get_env_path().exists(),
            "path": str(get_env_path()),
        },
        "logs": {
            "dir": str(get_logs_dir()),
            "exists": get_logs_dir().exists(),
        },
        "state_db": {
            "path": str(get_state_db_path()),
            "exists": get_state_db_path().exists(),
        },
        "model": {
            "provider": config.get("model", {}).get("provider", "unknown"),
            "default": config.get("model", {}).get("default", "unknown"),
        },
        "voice": {
            "gemini_live": {
                "enabled": config.get("voice", {}).get("gemini_live", {}).get("enabled", False),
                "model": config.get("voice", {}).get("gemini_live", {}).get("model", "unknown"),
                "api_key_configured": bool(get_env_value("GEMINI_API_KEY") or get_env_value("GOOGLE_API_KEY")),
            },
            "vapi": {
                "enabled": config.get("voice", {}).get("vapi", {}).get("enabled", False),
                "assistant_id": config.get("voice", {}).get("vapi", {}).get("assistant_id", ""),
                "api_key_configured": bool(get_env_value("VAPI_API_KEY")),
            },
            "discord": {
                "bot_token_configured": bool(get_env_value("DISCORD_BOT_TOKEN")),
                "app_id_configured": bool(get_env_value("DISCORD_APPLICATION_ID")),
                "guild_id": config.get("voice", {}).get("discord", {}).get("guild_id", ""),
            },
        },
        "mcp": {
            "enabled": config.get("mcp", {}).get("enabled", True),
            "servers": list(config.get("mcp", {}).get("servers", {}).keys()),
        },
        "memory": {
            "provider": config.get("memory", {}).get("provider", "unknown"),
            "honcho_enabled": config.get("honcho", {}).get("enabled", False),
            "honcho_host": config.get("honcho", {}).get("host", "unknown"),
        },
        "tools": {
            "tts": config.get("tts", {}).get("provider", "unknown"),
            "stt": config.get("stt", {}).get("provider", "unknown"),
            "web_search_configured": any(
                get_env_value(k) for k in ["EXA_API_KEY", "PARALLEL_API_KEY", "FIRECRAWL_API_KEY", "TAVILY_API_KEY", "SEARXNG_URL"]
            ),
            "image_gen_configured": bool(get_env_value("FAL_KEY") or get_env_value("OPENAI_API_KEY")),
        },
        "dependencies": {
            "python": sys.version.split()[0],
            "node": "available" if check_command("node") else "missing",
            "npm": "available" if check_command("npm") else "missing",
            "npx": "available" if check_command("npx") else "missing",
            "docker": "available" if check_command("docker") else "missing",
        },
        "services": get_service_status(),
    }

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        # Pretty print
        print(f"S0RA Agent v{status['version']}")
        print(f"Home: {status['sora_home']}")
        print()
        print("Config:")
        print(f"  config.yaml: {'✓' if status['config']['exists'] else '✗'} ({status['config']['path']})")
        print(f"  .env:        {'✓' if status['env']['exists'] else '✗'} ({status['env']['path']})")
        print()
        print("Model:")
        print(f"  Provider: {status['model']['provider']}")
        print(f"  Default:  {status['model']['default']}")
        print()
        print("Voice Bridges:")
        gem = status['voice']['gemini_live']
        print(f"  Gemini Live: {'Enabled' if gem['enabled'] else 'Disabled'} (model: {gem['model']}) {'✓' if gem['api_key_configured'] else '✗ API key'}")
        vapi = status['voice']['vapi']
        print(f"  Vapi:        {'Enabled' if vapi['enabled'] else 'Disabled'} (assistant: {vapi['assistant_id'] or 'none'}) {'✓' if vapi['api_key_configured'] else '✗ API key'}")
        disc = status['voice']['discord']
        print(f"  Discord:     {'✓' if disc['bot_token_configured'] else '✗'} Bot Token | {'✓' if disc['app_id_configured'] else '✗'} App ID | Guild: {disc['guild_id'] or 'none'}")
        print()
        print("MCP:")
        print(f"  Enabled:  {'Yes' if status['mcp']['enabled'] else 'No'}")
        print(f"  Servers:  {', '.join(status['mcp']['servers']) if status['mcp']['servers'] else 'None configured'}")
        print()
        print("Memory:")
        print(f"  Provider: {status['memory']['provider']}")
        print(f"  Honcho:   {'Enabled' if status['memory']['honcho_enabled'] else 'Disabled'} ({status['memory']['honcho_host']})")
        print()
        print("Tools:")
        print(f"  TTS: {status['tools']['tts']}")
        print(f"  STT: {status['tools']['stt']}")
        print(f"  Web Search: {'✓' if status['tools']['web_search_configured'] else '✗'}")
        print(f"  Image Gen:  {'✓' if status['tools']['image_gen_configured'] else '✗'}")
        print()
        print("Dependencies:")
        for name, avail in status['dependencies'].items():
            print(f"  {name}: {avail}")
        print()
        print("Services:")
        for name, state in status['services'].items():
            print(f"  {name}: {state}")

    return 0