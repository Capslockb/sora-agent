"""
Sora VOIP Bridge Plugin
=======================
Asterisk ARI + Dograh/Gemini Live integration for phone calls.
Registers CLI tools and Discord slash commands for voice call management.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

log = logging.getLogger("sora.voip")

# ──────────────────────────────────────────────
# Plugin registration
# ──────────────────────────────────────────────

PLUGIN_METADATA = {
    "name": "sora-voip",
    "version": "0.1.0",
    "description": "Asterisk ARI + Dograh/Gemini Live bridge for phone calls",
    "tools": [
        "sora_voice_sip",
        "sora_voice_ari",
        "sora_voice_call",
        "sora_voice_hangup",
        "sora_voice_status",
        "sora_voip_config",
    ],
    "commands": [
        "voice sip",
        "voice ari",
        "voice call",
        "voice hangup",
        "voice status",
        "voip config",
    ],
}

# Global bridge instance
_bridge_instance: Optional["VoipBridge"] = None
_config: Dict[str, Any] = {}


def register(ctx) -> None:
    """Entry point called by Sora CLI / Hermes plugin loader."""
    from .bridge import VoipBridge
    from .ari_client import AriClient
    from .rtp_handler import RtpHandler
    from .dograh_client import DograhClient

    global _bridge_instance, _config

    # Load config
    _config = _load_config(ctx)
    log.info("sora-voip plugin loading", extra={"config": _safe_config(_config)})

    # Initialize bridge
    _bridge_instance = VoipBridge(
        ari_client=AriClient(
            url=_config.get("asterisk_ari_url", "http://localhost:8088/ari"),
            username=_config.get("asterisk_username", "sora"),
            password=_config.get("asterisk_password", ""),
            app_name=_config.get("asterisk_app_name", "sora-bridge"),
        ),
        rtp_handler=RtpHandler(
            port_range=_config.get("rtp_port_range", "10000-20000"),
            sample_rate=_config.get("sample_rate", 48000),
        ),
        dograh_client=DograhClient(
            ws_url=_config.get("dograh_ws_url", "wss://dograh.local/ws"),
            api_key=_config.get("dograh_api_key", ""),
            model=_config.get("gemini_model", "gemini-2.0-flash-exp"),
        ),
        config=_config,
    )

    # Register CLI tools
    _register_tools(ctx)

    # Register Discord slash commands (if Discord gateway present)
    _register_discord_commands(ctx)

    # Start background tasks
    asyncio.create_task(_bridge_instance.start())

    log.info("sora-voip plugin loaded successfully")


def _load_config(ctx) -> Dict[str, Any]:
    """Load config from Sora/Hermes config system."""
    config = {}

    # Try Sora config first
    try:
        if hasattr(ctx, "config") and ctx.config:
            voip_cfg = ctx.config.get("voip", {})
            if voip_cfg:
                config.update(voip_cfg)
    except Exception:
        raise NotImplementedError("TODO")

    # Try Hermes config
    try:
        if hasattr(ctx, "hermes_config") and ctx.hermes_config:
            voip_cfg = ctx.hermes_config.get("plugins", {}).get("sora-voip", {})
            if voip_cfg:
                config.update(voip_cfg)
    except Exception:
        raise NotImplementedError("TODO")

    # Environment variable overrides
    env_mapping = {
        "ASTERISK_ARI_URL": "asterisk_ari_url",
        "ASTERISK_USERNAME": "asterisk_username",
        "ASTERISK_PASSWORD": "asterisk_password",
        "ASTERISK_APP_NAME": "asterisk_app_name",
        "DOGRAH_WS_URL": "dograh_ws_url",
        "DOGRAH_API_KEY": "dograh_api_key",
        "GEMINI_MODEL": "gemini_model",
        "SAMPLE_RATE": "sample_rate",
        "RTP_PORT_RANGE": "rtp_port_range",
        "AUTO_ANSWER": "auto_answer",
        "RECORD_CALLS": "record_calls",
        "RECORDING_DIR": "recording_dir",
    }

    for env_key, cfg_key in env_mapping.items():
        val = os.getenv(env_key)
        if val is not None:
            if cfg_key in ("sample_rate", "auto_answer", "record_calls"):
                val = val.lower() in ("true", "1", "yes", "on")
            elif cfg_key == "sample_rate":
                val = int(val)
            config[cfg_key] = val

    # Defaults
    defaults = {
        "asterisk_ari_url": "http://localhost:8088/ari",
        "asterisk_username": "sora",
        "asterisk_password": "",
        "asterisk_app_name": "sora-bridge",
        "dograh_ws_url": "wss://dograh.local/ws",
        "dograh_api_key": "",
        "gemini_model": "gemini-2.0-flash-exp",
        "sample_rate": 48000,
        "channels": 1,
        "rtp_port_range": "10000-20000",
        "auto_answer": True,
        "record_calls": False,
        "recording_dir": "~/.sora/recordings",
    }

    for k, v in defaults.items():
        config.setdefault(k, v)

    return config


def _safe_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Return config with secrets masked for logging."""
    safe = dict(cfg)
    for key in ("asterisk_password", "dograh_api_key"):
        if key in safe and safe[key]:
            safe[key] = "***"
    return safe


# ──────────────────────────────────────────────
# Tool registration
# ──────────────────────────────────────────────

def _register_tools(ctx) -> None:
    """Register Sora CLI tools."""

    @ctx.register_tool(name="sora_voice_sip")
    async def sora_voice_sip(
        action: str,  # "register" | "unregister" | "status"
        username: Optional[str] = None,
        password: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Manage SIP registration with Asterisk."""
        if not _bridge_instance:
            return {"error": "VOIP bridge not initialized"}

        if action == "register":
            return await _bridge_instance.sip_register(username, password, domain)
        elif action == "unregister":
            return await _bridge_instance.sip_unregister()
        elif action == "status":
            return _bridge_instance.sip_status()
        else:
            return {"error": f"Unknown action: {action}"}

    @ctx.register_tool(name="sora_voice_ari")
    async def sora_voice_ari(
        action: str,  # "connect" | "disconnect" | "status" | "apps"
        app_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Manage ARI connection and applications."""
        if not _bridge_instance:
            return {"error": "VOIP bridge not initialized"}

        if action == "connect":
            return await _bridge_instance.ari_connect(app_name)
        elif action == "disconnect":
            return await _bridge_instance.ari_disconnect()
        elif action == "status":
            return _bridge_instance.ari_status()
        elif action == "apps":
            return await _bridge_instance.ari_list_apps()
        else:
            return {"error": f"Unknown action: {action}"}

    @ctx.register_tool(name="sora_voice_call")
    async def sora_voice_call(
        number: str,
        caller_id: Optional[str] = None,
        auto_answer: Optional[bool] = None,
        record: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Originate an outbound call via Asterisk and connect to Dograh/Gemini."""
        if not _bridge_instance:
            return {"error": "VOIP bridge not initialized"}
        return await _bridge_instance.originate_call(
            number=number,
            caller_id=caller_id,
            auto_answer=auto_answer,
            record=record,
        )

    @ctx.register_tool(name="sora_voice_hangup")
    async def sora_voice_hangup(
        channel_id: Optional[str] = None,
        all_calls: bool = False,
    ) -> Dict[str, Any]:
        """Hang up active call(s)."""
        if not _bridge_instance:
            return {"error": "VOIP bridge not initialized"}
        return await _bridge_instance.hangup(channel_id=channel_id, all_calls=all_calls)

    @ctx.register_tool(name="sora_voice_status")
    async def sora_voice_status(
        detailed: bool = False,
    ) -> Dict[str, Any]:
        """Get VOIP bridge status: ARI, SIP, active calls, Dograh connection."""
        if not _bridge_instance:
            return {"error": "VOIP bridge not initialized"}
        return _bridge_instance.get_status(detailed=detailed)

    @ctx.register_tool(name="sora_voip_config")
    async def sora_voip_config(
        action: str,  # "show" | "set" | "reload"
        key: Optional[str] = None,
        value: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Manage VOIP configuration."""
        global _config, _bridge_instance

        if action == "show":
            return _safe_config(_config)
        elif action == "set":
            if not key:
                return {"error": "key required for set action"}
            _config[key] = value
            # Persist to config file
            _persist_config(_config)
            # Hot-reload relevant parts
            if _bridge_instance:
                await _bridge_instance.reload_config(_config)
            return {"ok": True, "key": key, "value": value}
        elif action == "reload":
            _config = _load_config(ctx)
            if _bridge_instance:
                await _bridge_instance.reload_config(_config)
            return {"ok": True, "config": _safe_config(_config)}
        else:
            return {"error": f"Unknown action: {action}"}


def _persist_config(config: Dict[str, Any]) -> None:
    """Persist config to Sora config file."""
    try:
        from sora_cli.config import ConfigManager
        mgr = ConfigManager()
        mgr.set("voip", config)
        mgr.save()
    except Exception as e:
        log.warning("Failed to persist VOIP config", extra={"error": str(e)})


def _register_discord_commands(ctx) -> None:
    """Register Discord slash commands if Discord gateway is available."""
    try:
        discord_bot = getattr(ctx, "discord_bot", None) or getattr(ctx, "bot", None)
        if not discord_bot:
            return

        @discord_bot.tree.command(name="voice-sip", description="Manage SIP registration")
        async def discord_voice_sip(interaction, action: str, username: str = None, password: str = None, domain: str = None):
            await interaction.response.defer(ephemeral=True)
            result = await _bridge_instance.sip_register(username, password, domain) if action == "register" else \
                     await _bridge_instance.sip_unregister() if action == "unregister" else \
                     _bridge_instance.sip_status()
            await interaction.followup.send(f"```json\n{result}\n```")

        @discord_bot.tree.command(name="voice-call", description="Place an outbound call")
        async def discord_voice_call(interaction, number: str, caller_id: str = None, record: bool = False):
            await interaction.response.defer(ephemeral=True)
            result = await _bridge_instance.originate_call(number, caller_id, record=record)
            await interaction.followup.send(f"```json\n{result}\n```")

        @discord_bot.tree.command(name="voice-hangup", description="Hang up active call")
        async def discord_voice_hangup(interaction, channel_id: str = None, all_calls: bool = False):
            await interaction.response.defer(ephemeral=True)
            result = await _bridge_instance.hangup(channel_id, all_calls)
            await interaction.followup.send(f"```json\n{result}\n```")

        @discord_bot.tree.command(name="voice-status", description="Show VOIP bridge status")
        async def discord_voice_status(interaction, detailed: bool = False):
            await interaction.response.defer(ephemeral=True)
            result = _bridge_instance.get_status(detailed=detailed)
            await interaction.followup.send(f"```json\n{result}\n```")

        log.info("Discord slash commands registered for sora-voip")
    except Exception as e:
        log.debug("Discord commands not registered (no Discord gateway)", extra={"error": str(e)})


# ──────────────────────────────────────────────
# Public API for external use
# ──────────────────────────────────────────────

def get_bridge() -> Optional["VoipBridge"]:
    """Get the global bridge instance, initializing if needed."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = _create_bridge()
    return _bridge_instance


def _create_bridge() -> "VoipBridge":
    """Create and initialize the VOIP bridge from config."""
    global _config
    from .bridge import VoipBridge
    from .ari_client import AriClient
    from .rtp_handler import RtpHandler
    from .dograh_client import DograhClient
    from sora_cli.config import load_config

    config = load_config()
    voip_config = config.get("voip", {})

    # Load config with defaults
    full_config = {
        "asterisk_ari_url": voip_config.get("asterisk_ari_url", "http://localhost:8088/ari"),
        "asterisk_username": voip_config.get("asterisk_username", "sora"),
        "asterisk_password": voip_config.get("asterisk_password", ""),
        "asterisk_app_name": voip_config.get("asterisk_app_name", "sora-bridge"),
        "dograh_ws_url": voip_config.get("dograh_ws_url", "wss://dograh.local/ws"),
        "dograh_api_key": voip_config.get("dograh_api_key", ""),
        "gemini_model": voip_config.get("gemini_model", "gemini-2.0-flash-exp"),
        "sample_rate": voip_config.get("sample_rate", 48000),
        "rtp_port_range": voip_config.get("rtp_port_range", "10000-20000"),
        "auto_answer": voip_config.get("auto_answer", True),
        "record_calls": voip_config.get("record_calls", False),
        "recording_dir": voip_config.get("recording_dir", "~/.sora/recordings"),
    }

    # Update global config for get_config()
    _config = full_config

    return VoipBridge(
        ari_client=AriClient(
            url=full_config["asterisk_ari_url"],
            username=full_config["asterisk_username"],
            password=full_config["asterisk_password"],
            app_name=full_config["asterisk_app_name"],
        ),
        rtp_handler=RtpHandler(
            port_range=full_config["rtp_port_range"],
            sample_rate=full_config["sample_rate"],
        ),
        dograh_client=DograhClient(
            ws_url=full_config["dograh_ws_url"],
            api_key=full_config["dograh_api_key"],
            model=full_config["gemini_model"],
        ),
        config=full_config,
    )


def get_config() -> Dict[str, Any]:
    """Get current VOIP config (secrets masked)."""
    return _safe_config(_config)


__all__ = [
    "register",
    "PLUGIN_METADATA",
    "get_bridge",
    "get_config",
]
