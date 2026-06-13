"""
S0RA Doctor CLI — Check configuration and dependencies.
"""

import subprocess
import sys
from pathlib import Path

from sora_cli.config import load_config, get_env_value
from sora_constants import get_sora_home, get_config_path, get_env_path
from sora_logging import setup_logging
from sora_cli.cli_output import print_error, print_success, print_warning, print_info

setup_logging("cli")


def check_command(cmd: str, name: str = None) -> bool:
    import shutil
    result = shutil.which(cmd) is not None
    label = name or cmd
    if result:
        print_success(f"{label}: found")
    else:
        print_error(f"{label}: NOT FOUND")
    return result


def check_python_package(pkg: str, name: str = None) -> bool:
    label = name or pkg
    try:
        __import__(pkg.replace("-", "_"))
        print_success(f"{label}: available")
        return True
    except ImportError:
        print_error(f"{label}: NOT INSTALLED")
        return False


def main(args) -> int:
    print("S0RA Doctor — System Health Check")
    print("=" * 50)
    print()

    all_ok = True

    # 1. SORA_HOME
    print_header("1. SORA_HOME")
    sora_home = get_sora_home()
    print_info(f"Path: {sora_home}")
    if sora_home.exists():
        print_success("Directory exists")
    else:
        print_warning("Directory does not exist (will be created on first run)")
    print()

    # 2. Config files
    print_header("2. Configuration")
    cfg_path = get_config_path()
    env_path = get_env_path()
    if cfg_path.exists():
        print_success(f"config.yaml: {cfg_path}")
    else:
        print_warning(f"config.yaml: not found (run 'sora setup')")
        all_ok = False

    if env_path.exists():
        print_success(f".env: {env_path}")
    else:
        print_warning(f".env: not found (run 'sora setup')")
        all_ok = False
    print()

    # 3. Core dependencies
    print_header("3. Core Dependencies")
    deps = [
        ("python3", "python3"),
        ("node", "Node.js"),
        ("npm", "npm"),
        ("npx", "npx"),
        ("git", "git"),
        ("docker", "Docker"),
    ]
    for cmd, name in deps:
        check_command(cmd, name)
    print()

    # 4. Python packages
    print_header("4. Python Packages")
    packages = [
        ("openai", "openai"),
        ("httpx", "httpx"),
        ("rich", "rich"),
        ("pydantic", "pydantic"),
        ("yaml", "PyYAML"),
        ("prompt_toolkit", "prompt_toolkit"),
        ("croniter", "croniter"),
        ("websockets", "websockets"),
        ("discord", "discord.py"),
        ("aiohttp", "aiohttp"),
        ("numpy", "numpy"),
        ("mcp", "mcp"),
    ]
    for pkg, name in packages:
        check_python_package(pkg, name)
    print()

    # 5. API Keys
    print_header("5. API Keys")
    keys = [
        ("OPENROUTER_API_KEY", "OpenRouter"),
        ("GEMINI_API_KEY", "Google Gemini"),
        ("GOOGLE_API_KEY", "Google API (alt)"),
        ("VAPI_API_KEY", "Vapi.ai"),
        ("DISCORD_BOT_TOKEN", "Discord Bot"),
        ("DISCORD_APPLICATION_ID", "Discord App ID"),
        ("ANTHROPIC_API_KEY", "Anthropic"),
        ("OPENAI_API_KEY", "OpenAI"),
        ("ELEVENLABS_API_KEY", "ElevenLabs"),
        ("EXA_API_KEY", "Exa"),
        ("PARALLEL_API_KEY", "Parallel Web"),
        ("FIRECRAWL_API_KEY", "Firecrawl"),
        ("TAVILY_API_KEY", "Tavily"),
        ("FAL_KEY", "FAL"),
    ]
    for env_var, name in keys:
        val = get_env_value(env_var)
        if val:
            masked = val[:8] + "..." + val[-4:] if len(val) > 12 else "***"
            print_success(f"{name}: {masked}")
        else:
            print_warning(f"{name}: not set")
    print()

    # 6. Voice Bridge Prerequisites
    print_header("6. Voice Bridge Prerequisites")
    # Check Discord.py voice support
    try:
        import discord
        import discord.voice_client
        print_success("discord.py[voice]: available")
    except ImportError:
        print_error("discord.py[voice]: NOT INSTALLED (install with: pip install 'discord.py[voice]')")
        all_ok = False

    # Check Opus
    try:
        import subprocess
        result = subprocess.run(["which", "opusenc"], capture_output=True)
        if result.returncode == 0:
            print_success("opusenc: available")
        else:
            print_warning("opusenc: not found (voice may not work properly)")
    except Exception:
        print_warning("opusenc: could not check")

    print()

    # 7. MCP Servers
    print_header("7. MCP Servers")
    config = load_config()
    servers = config.get("mcp", {}).get("servers", {})
    if servers:
        for name, server in servers.items():
            print_info(f"{name}: {server.get('command')} {' '.join(server.get('args', []))}")
    else:
        print_warning("No MCP servers configured")
    print()

    # Summary
    print_header("Summary")
    if all_ok:
        print_success("All critical checks passed!")
        return 0
    else:
        print_warning("Some issues found. Run 'sora setup' to configure missing items.")
        if args.fix:
            print_info("Auto-fix not yet implemented")
        return 1


def print_header(title: str):
    print()
    print(title)
    print("-" * len(title))