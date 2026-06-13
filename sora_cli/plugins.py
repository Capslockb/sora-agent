"""
S0RA Plugins CLI — Plugin management.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from sora_constants import get_plugins_dir, get_sora_home, get_config_path
from sora_cli.config import load_config, save_config
from sora_logging import setup_logging
from sora_cli.cli_output import print_error, print_success, print_info, print_warning

setup_logging("cli")

# Built-in plugin registry (mirrors Hermes plugin system)
BUNDLED_PLUGINS = {
    "discord-voice": {
        "description": "Gemini Live ↔ Discord voice bridge",
        "type": "voice",
        "enabled": False,
    },
    "discord-vapi": {
        "description": "Vapi.ai ↔ Discord voice bridge",
        "type": "voice",
        "enabled": False,
    },
    "mcp": {
        "description": "MCP server integration",
        "type": "mcp",
        "enabled": True,
    },
    "honcho": {
        "description": "Honcho memory integration",
        "type": "memory",
        "enabled": True,
    },
}


def list_plugins(args) -> int:
    config = load_config()
    enabled = config.get("plugins", {}).get("enabled", [])

    print("Installed Plugins:")
    print("=" * 80)

    plugins_dir = get_plugins_dir()
    user_plugins = {}
    if plugins_dir.exists():
        for plugin_dir in plugins_dir.iterdir():
            if plugin_dir.is_dir():
                plugin_yaml = plugin_dir / "plugin.yaml"
                if plugin_yaml.exists():
                    import yaml
                    with open(plugin_yaml) as f:
                        meta = yaml.safe_load(f) or {}
                    user_plugins[plugin_dir.name] = meta

    # Show bundled
    print("\nBundled:")
    for name, meta in BUNDLED_PLUGINS.items():
        status = "enabled" if name in enabled else "disabled"
        print(f"  {name:<20} [{status}] — {meta['description']}")

    # Show user
    if user_plugins:
        print("\nUser-installed:")
        for name, meta in user_plugins.items():
            status = "enabled" if name in enabled else "disabled"
            desc = meta.get("description", "No description")
            print(f"  {name:<20} [{status}] — {desc}")
    else:
        print("\nUser-installed: none")

    return 0


def enable_plugin(args) -> int:
    if not args.plugin_name:
        print_error("Usage: sora plugins enable <name>")
        return 1

    config = load_config()
    enabled = config.setdefault("plugins", {}).setdefault("enabled", [])

    if args.plugin_name not in enabled:
        enabled.append(args.plugin_name)
        save_config(config)
        print_success(f"Enabled plugin: {args.plugin_name}")
    else:
        print_info(f"Plugin already enabled: {args.plugin_name}")
    return 0


def disable_plugin(args) -> int:
    if not args.plugin_name:
        print_error("Usage: sora plugins disable <name>")
        return 1

    config = load_config()
    enabled = config.get("plugins", {}).get("enabled", [])

    if args.plugin_name in enabled:
        enabled.remove(args.plugin_name)
        save_config(config)
        print_success(f"Disabled plugin: {args.plugin_name}")
    else:
        print_info(f"Plugin not enabled: {args.plugin_name}")
    return 0


def install_plugin(args) -> int:
    if not args.plugin_name:
        print_error("Usage: sora plugins install <github_repo>")
        return 1

    repo = args.plugin_name
    plugins_dir = get_plugins_dir()
    plugins_dir.mkdir(parents=True, exist_ok=True)

    # Clone from GitHub
    repo_name = repo.split("/")[-1].replace(".git", "")
    target = plugins_dir / repo_name

    if target.exists():
        print_error(f"Plugin directory already exists: {target}")
        return 1

    print_info(f"Cloning {repo}...")
    try:
        subprocess.run(["git", "clone", f"https://github.com/{repo}.git", str(target)], check=True)
    except subprocess.CalledProcessError:
        print_error("Failed to clone repository")
        return 1

    # Check for plugin.yaml
    plugin_yaml = target / "plugin.yaml"
    if not plugin_yaml.exists():
        print_warning("No plugin.yaml found — plugin may not be recognized")

    print_success(f"Installed plugin: {repo_name}")
    print_info(f"Enable with: sora plugins enable {repo_name}")
    return 0


def remove_plugin(args) -> int:
    if not args.plugin_name:
        print_error("Usage: sora plugins remove <name>")
        return 1

    plugins_dir = get_plugins_dir()
    target = plugins_dir / args.plugin_name

    if not target.exists():
        print_error(f"Plugin not found: {args.plugin_name}")
        return 1

    # Disable first
    config = load_config()
    enabled = config.get("plugins", {}).get("enabled", [])
    if args.plugin_name in enabled:
        enabled.remove(args.plugin_name)
        save_config(config)

    # Remove directory
    shutil.rmtree(target)
    print_success(f"Removed plugin: {args.plugin_name}")
    return 0


def update_plugins(args) -> int:
    plugins_dir = get_plugins_dir()
    if not plugins_dir.exists():
        print_info("No user plugins to update")
        return 0

    updated = 0
    for plugin_dir in plugins_dir.iterdir():
        if plugin_dir.is_dir() and (plugin_dir / ".git").exists():
            print_info(f"Updating {plugin_dir.name}...")
            try:
                subprocess.run(["git", "-C", str(plugin_dir), "pull"], check=True, capture_output=True)
                print_success(f"  Updated {plugin_dir.name}")
                updated += 1
            except subprocess.CalledProcessError:
                print_warning(f"  Failed to update {plugin_dir.name}")

    if updated == 0:
        print_info("No plugins updated")
    return 0


def main(args) -> int:
    if args.plugins_command is None:
        print("Usage: sora plugins <list|enable|disable|install|remove|update>")
        return 1

    handlers = {
        "list": list_plugins,
        "enable": enable_plugin,
        "disable": disable_plugin,
        "install": install_plugin,
        "remove": remove_plugin,
        "update": update_plugins,
    }

    handler = handlers.get(args.plugins_command)
    if handler:
        return handler(args)
    else:
        print_error(f"Unknown plugins command: {args.plugins_command}")
        return 1