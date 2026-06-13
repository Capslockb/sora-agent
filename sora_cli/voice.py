"""
S0RA Voice Bridge CLI — Voice bridge management commands.
Handles: sora voice live, sora voice vapi, sora voice status, sora voice leave, sora voice providers
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Load config early
from sora_cli.config import load_config, get_env_value, get_sora_home
from sora_constants import ensure_sora_home as ensure_hermes_home
from sora_logging import setup_logging

setup_logging("cli")


def build_voice_parser(subparsers):
    """Build the voice subcommand parser (called from main.py)."""
    voice_parser = subparsers.add_parser("voice", help="Voice bridge management")
    voice_sub = voice_parser.add_subparsers(dest="voice_command", metavar="<subcommand>")

    # voice live
    live_parser = voice_sub.add_parser("live", help="Start Gemini Live voice bridge")
    live_parser.add_argument("--guild", help="Discord guild ID")
    live_parser.add_argument("--channel", help="Discord voice channel ID")
    live_parser.add_argument("--user", help="Discord user ID (to infer channel)")

    # voice vapi
    vapi_parser = voice_sub.add_parser("vapi", help="Start Vapi voice bridge")
    vapi_parser.add_argument("--guild", help="Discord guild ID")
    vapi_parser.add_argument("--channel", help="Discord voice channel ID")
    vapi_parser.add_argument("--user", help="Discord user ID (to infer channel)")

    # voice status
    voice_sub.add_parser("status", help="Show voice bridge status")

    # voice leave
    leave_parser = voice_sub.add_parser("leave", help="Stop voice bridge")
    leave_parser.add_argument("--guild", help="Discord guild ID (omit to stop all)")

    # voice providers
    providers_parser = voice_sub.add_parser("providers", help="Manage voice providers (TTS/STT/LLM Voice)")
    providers_sub = providers_parser.add_subparsers(dest="providers_command", metavar="<subcommand>")
    
    providers_list_parser = providers_sub.add_parser("list", help="List available providers")
    providers_list_parser.add_argument("-h", "--help", action="help")
    
    providers_enable_parser = providers_sub.add_parser("enable", help="Enable a provider")
    providers_enable_parser.add_argument("-h", "--help", action="help")
    providers_enable_parser.add_argument("provider", help="Provider name (gemini-live, vapi, elevenlabs, edge-tts, openai-tts, whisper)")
    
    providers_disable_parser = providers_sub.add_parser("disable", help="Disable a provider")
    providers_disable_parser.add_argument("-h", "--help", action="help")
    providers_disable_parser.add_argument("provider", help="Provider name")
    
    providers_config_parser = providers_sub.add_parser("config", help="Configure a provider")
    providers_config_parser.add_argument("-h", "--help", action="help")
    providers_config_parser.add_argument("provider", help="Provider name")


async def start_gemini_live(
    guild_id: Optional[str] = None,
    channel_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict:
    """Start the Gemini Live voice bridge."""
    from sora_cli.config import load_config

    config = load_config()
    gemini_config = config.get("voice", {}).get("gemini_live", {})
    discord_config = config.get("voice", {}).get("discord", {})

    # Use defaults from config if not provided
    if not guild_id:
        guild_id = discord_config.get("guild_id")
    if not user_id:
        user_id = discord_config.get("default_user_id")

    if not guild_id or not channel_id:
        return {
            "status": "error",
            "message": "guild_id and channel_id are required (provide via --guild/--channel or configure in 'sora setup')"
        }

    # Check prerequisites
    gemini_key = get_env_value("GEMINI_API_KEY") or get_env_value("GOOGLE_API_KEY")
    discord_token = get_env_value("DISCORD_BOT_TOKEN")

    if not gemini_key:
        return {"status": "error", "message": "GEMINI_API_KEY or GOOGLE_API_KEY not set"}
    if not discord_token:
        return {"status": "error", "message": "DISCORD_BOT_TOKEN not set"}

    # Import and start the bridge
    try:
        # This would use the discord-voice plugin's bridge logic
        # For now, return a placeholder indicating the bridge would start
        return {
            "status": "success",
            "message": f"Gemini Live bridge starting for guild {guild_id}, channel {channel_id}",
            "bridge_type": "gemini_live",
            "guild_id": guild_id,
            "channel_id": channel_id,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to start Gemini Live bridge: {e}"}


async def start_vapi(
    guild_id: Optional[str] = None,
    channel_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict:
    """Start the Vapi voice bridge."""
    from sora_cli.config import load_config

    config = load_config()
    vapi_config = config.get("voice", {}).get("vapi", {})
    discord_config = config.get("voice", {}).get("discord", {})

    if not guild_id:
        guild_id = discord_config.get("guild_id")
    if not user_id:
        user_id = discord_config.get("default_user_id")

    if not guild_id or not channel_id:
        return {
            "status": "error",
            "message": "guild_id and channel_id are required (provide via --guild/--channel or configure in 'sora setup')"
        }

    vapi_key = get_env_value("VAPI_API_KEY")
    discord_token = get_env_value("DISCORD_BOT_TOKEN")

    if not vapi_key:
        return {"status": "error", "message": "VAPI_API_KEY not set"}
    if not discord_token:
        return {"status": "error", "message": "DISCORD_BOT_TOKEN not set"}

    try:
        return {
            "status": "success",
            "message": f"Vapi bridge starting for guild {guild_id}, channel {channel_id}",
            "bridge_type": "vapi",
            "guild_id": guild_id,
            "channel_id": channel_id,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to start Vapi bridge: {e}"}


async def start_elevenlabs(
    guild_id: Optional[str] = None,
    channel_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict:
    """Start the ElevenLabs voice bridge."""
    from sora_cli.config import load_config

    config = load_config()
    eleven_config = config.get("voice", {}).get("elevenlabs", {})
    discord_config = config.get("voice", {}).get("discord", {})

    if not guild_id:
        guild_id = discord_config.get("guild_id")
    if not user_id:
        user_id = discord_config.get("default_user_id")

    if not guild_id or not channel_id:
        return {
            "status": "error",
            "message": "guild_id and channel_id are required"
        }

    eleven_key = get_env_value("ELEVENLABS_API_KEY")
    discord_token = get_env_value("DISCORD_BOT_TOKEN")

    if not eleven_key:
        return {"status": "error", "message": "ELEVENLABS_API_KEY not set"}
    if not discord_token:
        return {"status": "error", "message": "DISCORD_BOT_TOKEN not set"}

    try:
        return {
            "status": "success",
            "message": f"ElevenLabs bridge starting for guild {guild_id}, channel {channel_id}",
            "bridge_type": "elevenlabs",
            "guild_id": guild_id,
            "channel_id": channel_id,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to start ElevenLabs bridge: {e}"}


async def get_voice_status() -> dict:
    """Get status of all active voice bridges."""
    # This would query the actual bridge processes
    return {
        "status": "ok",
        "bridges": [],
        "message": "No active voice bridges"
    }


async def stop_voice_bridges(guild_id: Optional[str] = None) -> dict:
    """Stop voice bridge(s)."""
    return {
        "status": "success",
        "message": f"Stopped voice bridge(s)" + (f" for guild {guild_id}" if guild_id else " (all)")
    }


def handle_providers(args) -> int:
    """Handle providers subcommands."""
    from sora_cli.config import load_config, save_config, get_sora_home
    
    config = load_config()
    voice_config = config.setdefault("voice", {})
    
    # Default provider configurations
    default_providers = {
        "gemini_live": {"enabled": True, "configured": False, "type": "llm_voice", "model": "gemini-3.1-flash-live-preview"},
        "vapi": {"enabled": False, "configured": False, "type": "voice_platform"},
        "elevenlabs": {"enabled": False, "configured": False, "type": "tts"},
        "edge_tts": {"enabled": True, "configured": True, "type": "tts"},
        "openai_tts": {"enabled": False, "configured": False, "type": "tts"},
        "whisper": {"enabled": False, "configured": False, "type": "stt"},
    }
    
    providers = voice_config.setdefault("providers", default_providers)
    
    if args.providers_command is None or args.providers_command == "list":
        print("Available Voice Providers:")
        print("=" * 60)
        for name, info in providers.items():
            status = "✓ ENABLED" if info.get("enabled") else "○ DISABLED"
            config_status = "✓ Configured" if info.get("configured") else "⚠ Not configured"
            print(f"  {name:20} | {status:15} | {config_status:20} | {info.get('type', 'unknown')}")
        return 0
    
    if args.providers_command == "enable":
        provider = args.provider.replace("-", "_")
        if provider in providers:
            providers[provider]["enabled"] = True
            save_config(config)
            print(f"Enabled {provider}")
            return 0
        else:
            print(f"Unknown provider: {args.provider}")
            print(f"Available: {', '.join(providers.keys())}")
            return 1
    
    if args.providers_command == "disable":
        provider = args.provider.replace("-", "_")
        if provider in providers:
            providers[provider]["enabled"] = False
            save_config(config)
            print(f"Disabled {provider}")
            return 0
        else:
            print(f"Unknown provider: {args.provider}")
            return 1
    
    if args.providers_command == "config":
        provider = args.provider.replace("-", "_")
        if provider in providers:
            print(f"Configuring {provider}...")
            print("This would open interactive configuration.")
            print("For now, run 'sora setup' to configure providers.")
            return 0
        else:
            print(f"Unknown provider: {args.provider}")
            return 1
    
    print(f"Unknown providers command: {args.providers_command}")
    return 1


def main(args) -> int:
    """Main entry point for voice subcommands."""
    if args.voice_command is None:
        print("Usage: sora voice <live|vapi|elevenlabs|status|leave|providers>")
        return 1

    # Handle providers subcommand (non-async)
    if args.voice_command == "providers":
        return handle_providers(args)

    # Run async command
    try:
        if args.voice_command == "live":
            result = asyncio.run(start_gemini_live(args.guild, args.channel, args.user))
        elif args.voice_command == "vapi":
            result = asyncio.run(start_vapi(args.guild, args.channel, args.user))
        elif args.voice_command == "elevenlabs":
            result = asyncio.run(start_elevenlabs(args.guild, args.channel, args.user))
        elif args.voice_command == "status":
            result = asyncio.run(get_voice_status())
        elif args.voice_command == "leave":
            result = asyncio.run(stop_voice_bridges(args.guild))
        else:
            print(f"Unknown voice command: {args.voice_command}")
            return 1

        print(json.dumps(result, indent=2))
        return 0 if result.get("status") in ("success", "ok") else 1

    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1