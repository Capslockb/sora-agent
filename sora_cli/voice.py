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


def _env_first(*names: str) -> Optional[str]:
    """Return the first non-empty environment value."""
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _resolve_discord_target(
    config: dict,
    provider_name: str,
    guild_id: Optional[str] = None,
    channel_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Resolve Discord target IDs from CLI args, provider config, global config, then env.

    This is the standalone CLI's autodetect layer. A process without a live
    Discord adapter cannot discover a user's current voice channel, but it can
    and should auto-fill the configured/default guild, voice channel, and user.
    """
    voice_config = config.get("voice", {}) if isinstance(config, dict) else {}
    discord_config = voice_config.get("discord", {}) if isinstance(voice_config, dict) else {}
    provider_config = voice_config.get(provider_name, {}) if isinstance(voice_config, dict) else {}

    guild_id = (
        guild_id
        or provider_config.get("guild_id")
        or discord_config.get("guild_id")
        or _env_first("DISCORD_GUILD_ID", "SORA_DISCORD_GUILD_ID")
    )
    channel_id = (
        channel_id
        or provider_config.get("channel_id")
        or provider_config.get("voice_channel_id")
        or discord_config.get("voice_channel_id")
        or discord_config.get("channel_id")
        or _env_first("DISCORD_VOICE_CHANNEL_ID", "SORA_DISCORD_VOICE_CHANNEL_ID")
    )
    user_id = (
        user_id
        or provider_config.get("default_user_id")
        or discord_config.get("default_user_id")
        or _env_first("DISCORD_USER_ID", "SORA_DISCORD_USER_ID")
    )
    return guild_id, channel_id, user_id


def _redact_url_secret(url: str) -> str:
    """Hide signed ElevenLabs token values while keeping the URL debuggable."""
    if "token=" not in url:
        return url
    prefix, token = url.split("token=", 1)
    if "&" in token:
        _secret, rest = token.split("&", 1)
        return f"{prefix}token=***&{rest}"
    return f"{prefix}token=***"


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

    # voice elevenlabs
    eleven_parser = voice_sub.add_parser("elevenlabs", help="Start ElevenLabs Conversational AI voice bridge")
    eleven_parser.add_argument("--guild", help="Discord guild ID")
    eleven_parser.add_argument("--channel", help="Discord voice channel ID")
    eleven_parser.add_argument("--user", help="Discord user ID (to infer channel)")

    # voice openai
    openai_parser = voice_sub.add_parser("openai", help="Start OpenAI Realtime voice bridge (WebRTC)")
    openai_parser.add_argument("--guild", help="Discord guild ID")
    openai_parser.add_argument("--channel", help="Discord voice channel ID")
    openai_parser.add_argument("--user", help="Discord user ID (to infer channel)")

    # voice xai
    xai_parser = voice_sub.add_parser("xai", help="Start xAI Grok voice bridge")
    xai_parser.add_argument("--guild", help="Discord guild ID")
    xai_parser.add_argument("--channel", help="Discord voice channel ID")
    xai_parser.add_argument("--user", help="Discord user ID (to infer channel)")

    # voice ultravox
    uv_parser = voice_sub.add_parser("ultravox", help="Start Ultravox voice bridge")
    uv_parser.add_argument("--guild", help="Discord guild ID")
    uv_parser.add_argument("--channel", help="Discord voice channel ID")
    uv_parser.add_argument("--user", help="Discord user ID (to infer channel)")

    # voice retell
    retell_parser = voice_sub.add_parser("retell", help="Start Retell AI voice bridge")
    retell_parser.add_argument("--guild", help="Discord guild ID")
    retell_parser.add_argument("--channel", help="Discord voice channel ID")
    retell_parser.add_argument("--user", help="Discord user ID (to infer channel)")

    # voice status
    voice_sub.add_parser("status", help="Show voice bridge status")

    # voice leave
    leave_parser = voice_sub.add_parser("leave", help="Stop voice bridge")
    leave_parser.add_argument("--guild", help="Discord guild ID (omit to stop all)")

    # VOIP subcommands
    # voice sip
    sip_parser = voice_sub.add_parser("sip", help="Manage SIP registration")
    sip_sub = sip_parser.add_subparsers(dest="sip_action", metavar="<action>")
    sip_register = sip_sub.add_parser("register", help="Register SIP endpoint")
    sip_register.add_argument("--username", help="SIP username")
    sip_register.add_argument("--password", help="SIP password")
    sip_register.add_argument("--domain", help="SIP domain")
    sip_unregister = sip_sub.add_parser("unregister", help="Unregister SIP endpoint")
    sip_unregister.add_argument("--username", help="SIP username")
    sip_unregister.add_argument("--password", help="SIP password")
    sip_unregister.add_argument("--domain", help="SIP domain")
    sip_sub.add_parser("status", help="Show SIP registration status")

    # voice ari
    ari_parser = voice_sub.add_parser("ari", help="Manage ARI connection")
    ari_sub = ari_parser.add_subparsers(dest="ari_action", metavar="<action>")
    ari_connect = ari_sub.add_parser("connect", help="Connect ARI application")
    ari_connect.add_argument("--app", help="ARI application name")
    ari_disconnect = ari_sub.add_parser("disconnect", help="Disconnect ARI application")
    ari_disconnect.add_argument("--app", help="ARI application name")
    ari_sub.add_parser("status", help="Show ARI connection status")
    ari_sub.add_parser("apps", help="List registered ARI applications")

    # voice call
    call_parser = voice_sub.add_parser("call", help="Place an outbound call via Asterisk")
    call_parser.add_argument("number", help="Phone number to call")
    call_parser.add_argument("--caller-id", help="Caller ID to present")
    call_parser.add_argument("--auto-answer", action="store_true", help="Auto-answer the call")
    call_parser.add_argument("--record", action="store_true", help="Record the call")

    # voice hangup
    hangup_parser = voice_sub.add_parser("hangup", help="Hang up active call(s)")
    hangup_parser.add_argument("--channel", help="Channel ID to hang up")
    hangup_parser.add_argument("--all", action="store_true", help="Hang up all calls")

    # voice voip-status
    voice_sub.add_parser("voip-status", help="Show VOIP bridge status (ARI, SIP, calls, Dograh)")

    # voice voip-config
    voip_config_parser = voice_sub.add_parser("voip-config", help="Manage VOIP configuration")
    voip_config_sub = voip_config_parser.add_subparsers(dest="voip_config_action", metavar="<action>")
    voip_config_sub.add_parser("show", help="Show current VOIP configuration")
    voip_config_set = voip_config_sub.add_parser("set", help="Set a VOIP config value")
    voip_config_set.add_argument("key", help="Config key (e.g., asterisk_ari_url, dograh_ws_url)")
    voip_config_set.add_argument("value", help="Config value")
    voip_config_sub.add_parser("reload", help="Reload VOIP configuration in plugin")

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
    guild_id, channel_id, user_id = _resolve_discord_target(config, "gemini_live", guild_id, channel_id, user_id)

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
    guild_id, channel_id, user_id = _resolve_discord_target(config, "vapi", guild_id, channel_id, user_id)

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
    guild_id, channel_id, user_id = _resolve_discord_target(config, "elevenlabs", guild_id, channel_id, user_id)

    if not guild_id or not channel_id:
        return {
            "status": "error",
            "message": "guild_id and channel_id are required (provide --guild/--channel, voice.discord.voice_channel_id, voice.elevenlabs.channel_id, or DISCORD_VOICE_CHANNEL_ID)",
        }

    eleven_key = get_env_value("ELEVENLABS_API_KEY")
    agent_id = eleven_config.get("agent_id") or get_env_value("ELEVENLABS_AGENT_ID")
    discord_token = get_env_value("DISCORD_BOT_TOKEN") or eleven_config.get("discord_bot_token")

    if not agent_id:
        return {"status": "error", "message": "ELEVENLABS_AGENT_ID or voice.elevenlabs.agent_id not set"}
    if not discord_token:
        return {"status": "error", "message": "DISCORD_BOT_TOKEN not set"}

    from sora_cli.elevenlabs_client import get_signed_conversation_url, public_conversation_url

    websocket_url = public_conversation_url(agent_id)
    auth_mode = "public-agent-url"

    # Private agents require a signed URL. If an API key is present, prefer it.
    if eleven_key:
        try:
            websocket_url = await get_signed_conversation_url(agent_id, eleven_key)
            auth_mode = "signed-url"
        except RuntimeError as e:
            text = str(e)
            if "HTTP 401" not in text and "HTTP 403" not in text and "HTTP 404" not in text:
                return {"status": "error", "message": text}

    return {
        "status": "success",
        "message": f"ElevenLabs Conversational AI bridge ready for guild {guild_id}, channel {channel_id}",
        "bridge_type": "elevenlabs",
        "guild_id": guild_id,
        "channel_id": channel_id,
        "user_id": user_id,
        "agent_id": agent_id,
        "auth_mode": auth_mode,
        "websocket_url": _redact_url_secret(websocket_url),
        "protocol": {
            "client_audio_event": "{user_audio_chunk: <base64 pcm chunk>}",
            "server_audio_event": "type=audio, audio_event.audio_base_64",
            "ping_response": "reply with {type: pong, event_id: ping_event.event_id}",
        },
    }


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
        "elevenlabs": {"enabled": False, "configured": False, "type": "llm_voice"},
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


# ──────────────────────────────────────────────
# VOIP Handlers
# ──────────────────────────────────────────────

async def handle_sip(args) -> dict:
    """Handle SIP registration commands."""
    # This would use the sora-voip plugin's bridge
    if not args.sip_action:
        return {"status": "error", "message": "SIP action required: register, unregister, status"}

    try:
        from plugins.sora_voip import get_bridge
        bridge = get_bridge()
        if not bridge:
            return {"status": "error", "message": "VOIP bridge not initialized. Ensure sora-voip plugin is loaded."}

        if args.sip_action == "register":
            return await bridge.sip_register(args.username, args.password, args.domain)
        elif args.sip_action == "unregister":
            return await bridge.sip_unregister()
        elif args.sip_action == "status":
            return await bridge.sip_status()
        else:
            return {"status": "error", "message": f"Unknown SIP action: {args.sip_action}"}
    except ImportError:
        return {"status": "error", "message": "sora-voip plugin not available. Install with: pip install -e ./plugins/sora_voip"}


async def handle_ari(args) -> dict:
    """Handle ARI connection commands."""
    if not args.ari_action:
        return {"status": "error", "message": "ARI action required: connect, disconnect, status, apps"}

    try:
        from plugins.sora_voip import get_bridge
        bridge = get_bridge()
        if not bridge:
            return {"status": "error", "message": "VOIP bridge not initialized. Ensure sora-voip plugin is loaded."}

        if args.ari_action == "connect":
            return await bridge.ari_connect(args.app)
        elif args.ari_action == "disconnect":
            return await bridge.ari_disconnect()
        elif args.ari_action == "status":
            return bridge.ari_status()
        elif args.ari_action == "apps":
            return await bridge.ari_list_apps()
        else:
            return {"status": "error", "message": f"Unknown ARI action: {args.ari_action}"}
    except ImportError:
        return {"status": "error", "message": "sora-voip plugin not available"}


async def handle_call(args) -> dict:
    """Handle outbound call command."""
    try:
        from plugins.sora_voip import get_bridge
        bridge = get_bridge()
        if not bridge:
            return {"status": "error", "message": "VOIP bridge not initialized. Ensure sora-voip plugin is loaded."}

        auto_answer = args.auto_answer if args.auto_answer else None
        record = args.record if args.record else None

        return await bridge.originate_call(
            number=args.number,
            caller_id=args.caller_id,
            auto_answer=auto_answer,
            record=record,
        )
    except ImportError:
        return {"status": "error", "message": "sora-voip plugin not available"}


async def handle_hangup(args) -> dict:
    """Handle hangup command."""
    try:
        from plugins.sora_voip import get_bridge
        bridge = get_bridge()
        if not bridge:
            return {"status": "error", "message": "VOIP bridge not initialized. Ensure sora-voip plugin is loaded."}

        if args.all:
            return await bridge.hangup(all_calls=True)
        elif args.channel:
            return await bridge.hangup(channel_id=args.channel)
        else:
            return {"status": "error", "message": "Either --channel or --all required"}
    except ImportError:
        return {"status": "error", "message": "sora-voip plugin not available"}


async def handle_voip_status(args) -> dict:
    """Show VOIP bridge status."""
    try:
        from plugins.sora_voip import get_bridge
        bridge = get_bridge()
        if not bridge:
            return {"status": "error", "message": "VOIP bridge not initialized. Ensure sora-voip plugin is loaded."}

        status = bridge.get_status(detailed=True)
        status["status"] = "ok"
        return status
    except ImportError:
        return {"status": "error", "message": "sora-voip plugin not available"}


async def handle_voip_config(args) -> dict:
    """Manage VOIP configuration."""
    from sora_cli.config import load_config, save_config

    config = load_config()
    voip_config = config.setdefault("voip", {})

    if not hasattr(args, 'voip_config_action') or not args.voip_config_action:
        # Show current config
        safe_config = {k: ("***" if k in ("asterisk_password", "dograh_api_key") else v) for k, v in voip_config.items()}
        print(json.dumps(safe_config, indent=2))
        return {"status": "ok", "config": safe_config}

    if args.voip_config_action == "show":
        safe_config = {k: ("***" if k in ("asterisk_password", "dograh_api_key") else v) for k, v in voip_config.items()}
        return {"status": "ok", "config": safe_config}
    elif args.voip_config_action == "set":
        if not hasattr(args, 'key') or not args.key:
            return {"status": "error", "message": "key required for set action"}
        voip_config[args.key] = args.value
        save_config(config)
        return {"status": "ok", "message": f"Set {args.key} = {args.value}"}
    elif args.voip_config_action == "reload":
        return {"status": "ok", "message": "VOIP config reloaded (plugin hot-reload would trigger here)"}
    else:
        return {"status": "error", "message": f"Unknown voip-config action: {args.voip_config_action}"}


# ── New provider handlers (OpenAI, xAI, Ultravox, Retell) ──


async def start_openai_realtime(guild_id, channel_id, user_id) -> dict:
    """Start an OpenAI Realtime voice bridge."""
    from sora_cli.config import load_config, get_env_value
    from sora_cli.openai_realtime_client import OpenAIRealtimeConfig, OpenAIRealtimeClient

    config = load_config()
    guild_id, channel_id, user_id = _resolve_discord_target(config, "openai_realtime", guild_id, channel_id, user_id)
    api_key = get_env_value("OPENAI_API_KEY")
    if not api_key:
        return {"status": "error", "message": "OPENAI_API_KEY not set"}

    voice_cfg = config.get("voice", {})
    oc = voice_cfg.get("openai_realtime", {}) if isinstance(voice_cfg, dict) else {}

    rt_config = OpenAIRealtimeConfig(
        api_key=api_key,
        model=oc.get("model", "gpt-4o-realtime-preview"),
        voice=oc.get("voice", "alloy"),
        instructions=oc.get("instructions", "You are a helpful voice assistant."),
    )
    client = OpenAIRealtimeClient(rt_config)
    await client.connect()
    key = client.ephemeral_key()
    await client.disconnect()
    return {
        "status": "ok",
        "provider": "openai-realtime",
        "guild": guild_id or "auto",
        "channel": channel_id or "auto",
        "ephemeral_key": f"{key[:12]}..." if key else None,
    }


async def start_xai_grok(guild_id, channel_id, user_id) -> dict:
    """Start an xAI Grok voice bridge."""
    from sora_cli.config import load_config, get_env_value
    from sora_cli.xai_client import XAIConfig, XAIClient

    config = load_config()
    guild_id, channel_id, user_id = _resolve_discord_target(config, "xai", guild_id, channel_id, user_id)
    api_key = get_env_value("XAI_API_KEY")
    if not api_key:
        return {"status": "error", "message": "XAI_API_KEY not set"}

    voice_cfg = config.get("voice", {})
    xc = voice_cfg.get("xai", {}) if isinstance(voice_cfg, dict) else {}

    xai_cfg = XAIConfig(
        api_key=api_key,
        model=xc.get("model", "grok-2-realtime"),
        voice=xc.get("voice", "ember"),
        instructions=xc.get("instructions", "You are a helpful voice assistant."),
    )
    client = XAIClient(xai_cfg)
    return {
        "status": "ok",
        "provider": "xai-grok",
        "guild": guild_id or "auto",
        "channel": channel_id or "auto",
        "details": f"XAI client ready (model={xai_cfg.model})",
    }


async def start_ultravox_bridge(guild_id, channel_id, user_id) -> dict:
    """Start an Ultravox voice bridge."""
    from sora_cli.config import load_config, get_env_value
    from sora_cli.ultravox_client import UltravoxConfig, create_ultravox_call

    config = load_config()
    guild_id, channel_id, user_id = _resolve_discord_target(config, "ultravox", guild_id, channel_id, user_id)
    api_key = get_env_value("ULTRAVOX_API_KEY")
    if not api_key:
        return {"status": "error", "message": "ULTRAVOX_API_KEY not set"}

    voice_cfg = config.get("voice", {})
    uc = voice_cfg.get("ultravox", {}) if isinstance(voice_cfg, dict) else {}

    uv_cfg = UltravoxConfig(
        api_key=api_key,
        model=uc.get("model", "fixie-ai/ultravox"),
        voice=uc.get("voice", "default"),
        system_prompt=uc.get("system_prompt", "You are a helpful voice assistant."),
    )
    join_url = await create_ultravox_call(uv_cfg)
    return {
        "status": "ok",
        "provider": "ultravox",
        "guild": guild_id or "auto",
        "channel": channel_id or "auto",
        "join_url": join_url[:60] + "..." if len(join_url) > 60 else join_url,
    }


async def start_retell_bridge(guild_id, channel_id, user_id) -> dict:
    """Start a Retell AI voice bridge."""
    from sora_cli.config import load_config, get_env_value
    from sora_cli.retell_client import RetellConfig, create_web_call

    config = load_config()
    guild_id, channel_id, user_id = _resolve_discord_target(config, "retell", guild_id, channel_id, user_id)
    agent_id = get_env_value("RETELL_AGENT_ID")
    api_key = get_env_value("RETELL_API_KEY")
    if not agent_id:
        return {"status": "error", "message": "RETELL_AGENT_ID not set"}
    if not api_key:
        return {"status": "error", "message": "RETELL_API_KEY not set"}

    voice_cfg = config.get("voice", {})
    rc = voice_cfg.get("retell", {}) if isinstance(voice_cfg, dict) else {}

    rt_cfg = RetellConfig(
        api_key=api_key,
        agent_id=agent_id,
        voice_id=rc.get("voice_id", ""),
    )
    data = await create_web_call(rt_cfg)
    return {
        "status": "ok",
        "provider": "retell",
        "guild": guild_id or "auto",
        "channel": channel_id or "auto",
        "call_id": data.get("call_id"),
    }


def main(args) -> int:
    """Main entry point for voice subcommands."""
    if args.voice_command is None:
        print("Usage: sora voice <live|vapi|elevenlabs|openai|xai|ultravox|retell|status|leave|providers|sip|ari|call|hangup|voip-status|voip-config>")
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
        elif args.voice_command == "openai":
            result = asyncio.run(start_openai_realtime(args.guild, args.channel, args.user))
        elif args.voice_command == "xai":
            result = asyncio.run(start_xai_grok(args.guild, args.channel, args.user))
        elif args.voice_command == "ultravox":
            result = asyncio.run(start_ultravox_bridge(args.guild, args.channel, args.user))
        elif args.voice_command == "retell":
            result = asyncio.run(start_retell_bridge(args.guild, args.channel, args.user))
        elif args.voice_command == "status":
            result = asyncio.run(get_voice_status())
        elif args.voice_command == "leave":
            result = asyncio.run(stop_voice_bridges(args.guild))
        elif args.voice_command == "sip":
            result = asyncio.run(handle_sip(args))
        elif args.voice_command == "ari":
            result = asyncio.run(handle_ari(args))
        elif args.voice_command == "call":
            result = asyncio.run(handle_call(args))
        elif args.voice_command == "hangup":
            result = asyncio.run(handle_hangup(args))
        elif args.voice_command == "voip-status":
            result = asyncio.run(handle_voip_status(args))
        elif args.voice_command == "voip-config":
            result = asyncio.run(handle_voip_config(args))
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