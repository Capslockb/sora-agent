"""
Sora VOIP Plugin for Hermes
Registers VOIP bridge tools and commands.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from hermes.hermes import Hermes

logger = logging.getLogger("sora_voip")


# Global bridge instance
_bridge = None
_bridge_task = None


async def _get_bridge():
    """Get or create the VOIP bridge instance."""
    global _bridge, _bridge_task
    if _bridge is None:
        from .bridge import VoipBridge, VoipConfig

        config = VoipConfig(
            ari_url=os.getenv("SORA_ARI_URL", "http://localhost:8088/ari"),
            ari_user=os.getenv("SORA_ARI_USER", "sora"),
            ari_password=os.getenv("SORA_ARI_PASSWORD", ""),
            app_name=os.getenv("SORA_ARI_APP", "sora"),
            external_media_host=os.getenv("SORA_EXTERNAL_MEDIA_HOST", "0.0.0.0"),
            external_media_port=int(os.getenv("SORA_EXTERNAL_MEDIA_PORT", "5000")),
            dograh_ws_url=os.getenv("SORA_DOGRAH_WS_URL", ""),
            dograh_api_key=os.getenv("SORA_DOGRAH_API_KEY", ""),
            gemini_model=os.getenv("SORA_GEMINI_MODEL", "gemini-2.0-flash-exp"),
            gemini_voice=os.getenv("SORA_GEMINI_VOICE", "Puck"),
            gemini_temperature=float(os.getenv("SORA_GEMINI_TEMPERATURE", "0.7")),
            http_host=os.getenv("SORA_HTTP_HOST", "0.0.0.0"),
            http_port=int(os.getenv("SORA_HTTP_PORT", "18944")),
        )

        if not config.dograh_ws_url:
            raise RuntimeError("SORA_DOGRAH_WS_URL environment variable is required")

        _bridge = VoipBridge(config)
        _bridge_task = asyncio.create_task(_bridge.start())
        # Give it a moment to start
        await asyncio.sleep(0.5)

    return _bridge


async def sora_voip_start(ctx, *, dograh_ws_url: str = "", gemini_model: str = "") -> dict:
    """
    Start the Sora VOIP bridge (Asterisk + Dograh + Gemini Live).
    If already running, returns current status.

    Args:
        dograh_ws_url: Dograh WebSocket URL (overrides env)
        gemini_model: Gemini model to use (overrides env)
    """
    global _bridge, _bridge_task

    if _bridge is not None:
        return {"status": "already_running", "bridge": "sora-voip"}

    # Override config from args if provided
    if dograh_ws_url:
        os.environ["SORA_DOGRAH_WS_URL"] = dograh_ws_url
    if gemini_model:
        os.environ["SORA_GEMINI_MODEL"] = gemini_model

    try:
        bridge = await _get_bridge()
        return {
            "status": "started",
            "bridge": "sora-voip",
            "http_api": f"http://{bridge.config.http_host}:{bridge.config.http_port}",
            "health_endpoint": f"http://{bridge.config.http_host}:{bridge.config.http_port}/health",
        }
    except Exception as e:
        logger.error(f"Failed to start VOIP bridge: {e}")
        return {"status": "error", "error": str(e)}


async def sora_voip_stop(ctx) -> dict:
    """Stop the Sora VOIP bridge."""
    global _bridge, _bridge_task

    if _bridge is None:
        return {"status": "not_running"}

    try:
        await _bridge.stop()
        _bridge = None
        _bridge_task = None
        return {"status": "stopped", "bridge": "sora-voip"}
    except Exception as e:
        logger.error(f"Failed to stop VOIP bridge: {e}")
        return {"status": "error", "error": str(e)}


async def sora_voip_status(ctx) -> dict:
    """Get VOIP bridge health and active calls."""
    if _bridge is None:
        return {
            "status": "stopped",
            "bridge": "sora-voip",
            "active_calls": 0,
        }

    try:
        # Fetch from bridge's HTTP API
        import aiohttp
        url = f"http://{_bridge.config.http_host}:{_bridge.config.http_port}/health"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                else:
                    return {"status": "error", "http_status": resp.status}
    except Exception as e:
        logger.error(f"VOIP status check failed: {e}")
        return {"status": "error", "error": str(e)}


async def sora_voip_calls(ctx) -> dict:
    """List active VOIP calls with details."""
    if _bridge is None:
        return {"status": "stopped", "calls": []}

    try:
        import aiohttp
        url = f"http://{_bridge.config.http_host}:{_bridge.config.http_port}/calls"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"status": "error", "http_status": resp.status}
    except Exception as e:
        logger.error(f"VOIP calls list failed: {e}")
        return {"status": "error", "error": str(e)}


async def sora_voip_hangup(ctx, *, call_id: str) -> dict:
    """Hang up a specific VOIP call by call_id."""
    if _bridge is None:
        return {"status": "error", "error": "bridge not running"}

    try:
        import aiohttp
        url = f"http://{_bridge.config.http_host}:{_bridge.config.http_port}/calls/{call_id}/hangup"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"status": "error", "http_status": resp.status}
    except Exception as e:
        logger.error(f"VOIP hangup failed: {e}")
        return {"status": "error", "error": str(e)}


async def sora_voip_control(ctx, *, call_id: str, action: str) -> dict:
    """
    Control a VOIP call (mute/unmute).

    Args:
        call_id: Call ID from sora_voip_calls
        action: "mute" or "unmute"
    """
    if _bridge is None:
        return {"status": "error", "error": "bridge not running"}

    if action not in ("mute", "unmute"):
        return {"status": "error", "error": "action must be 'mute' or 'unmute'"}

    try:
        import aiohttp
        url = f"http://{_bridge.config.http_host}:{_bridge.config.http_port}/control"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"action": action, "call_id": call_id}, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"status": "error", "http_status": resp.status}
    except Exception as e:
        logger.error(f"VOIP control failed: {e}")
        return {"status": "error", "error": str(e)}


def register(ctx: Hermes) -> None:
    """Register VOIP tools with Hermes."""
    ctx.register_tool(sora_voip_start, name="sora_voip_start")
    ctx.register_tool(sora_voip_stop, name="sora_voip_stop")
    ctx.register_tool(sora_voip_status, name="sora_voip_status")
    ctx.register_tool(sora_voip_calls, name="sora_voip_calls")
    ctx.register_tool(sora_voip_hangup, name="sora_voip_hangup")
    ctx.register_tool(sora_voip_control, name="sora_voip_control")

    logger.info("Sora VOIP plugin registered (6 tools)")