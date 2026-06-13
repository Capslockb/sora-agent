"""
Sora Web Dashboard Backend API

FastAPI server providing REST endpoints for the web dashboard.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add sora_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sora_cli.config import (
    load_config, save_config, cfg_get, cfg_set,
    get_env_value, save_env_value, get_config_path
)
from sora_cli.sora_state import get_state
from sora_constants import get_default_sora_root


app = FastAPI(title="S0RA Agent API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---

class VoiceStartRequest(BaseModel):
    type: str  # gemini, vapi, elevenlabs, voip
    guildId: Optional[str] = None
    channelId: Optional[str] = None
    assistantId: Optional[str] = None
    agentId: Optional[str] = None
    ariUrl: Optional[str] = None
    ariUser: Optional[str] = None
    ariPassword: Optional[str] = None
    dograhWs: Optional[str] = None


class ProviderSelectRequest(BaseModel):
    category: str  # llm_voice, tts, stt
    provider: str


class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]


class EnvUpdateRequest(BaseModel):
    env: Dict[str, str]


class McpStartRequest(BaseModel):
    transport: str = "stdio"
    port: int = 3000


class McpWsStartRequest(BaseModel):
    host: str = "0.0.0.0"
    port: int = 3001


# --- Helper Functions ---

def get_sora_config() -> Dict[str, Any]:
    """Load Sora configuration."""
    return load_config()


def save_sora_config(config: Dict[str, Any]) -> None:
    """Save Sora configuration."""
    save_config(config)


def get_env_vars() -> Dict[str, str]:
    """Get all relevant environment variables."""
    keys = [
        'GEMINI_API_KEY', 'GOOGLE_API_KEY', 'VAPI_API_KEY', 'VAPI_PRIVATE_KEY',
        'ELEVENLABS_API_KEY', 'ELEVENLABS_AGENT_ID', 'OPENAI_API_KEY',
        'MINIMAX_API_KEY', 'MINIMAX_GROUP_ID', 'MISTRAL_API_KEY',
        'DISCORD_TOKEN', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID',
        'GITHUB_TOKEN', 'HONCHO_API_KEY', 'SORA_ARI_URL', 'SORA_ARI_USER',
        'SORA_ARI_PASSWORD', 'SORA_DOGRAH_WS_URL', 'SORA_DOGRAH_API_KEY',
    ]
    return {k: get_env_value(k) or '' for k in keys}


# --- Health & Status Endpoints ---

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "sora-api", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/status")
async def status():
    """Get overall system status."""
    config = get_sora_config()
    state = get_state()

    voice_config = cfg_get(config, "voice", default={})
    mcp_config = cfg_get(config, "mcp", default={})
    network_config = cfg_get(config, "network", default={})

    # Check voice bridge
    voice_status = "stopped"
    voice_type = "none"
    voice_model = "—"
    active_calls = 0

    if voice_config.get("provider"):
        voice_status = "configured"
        voice_type = voice_config.get("provider", "gemini-live")
        voice_model = voice_config.get("gemini_live", {}).get("model", "gemini-2.0-flash-exp")

    # Check MCP
    mcp_status = "stopped"
    mcp_transport = "stdio"
    mcp_port = 3000
    if mcp_config.get("auto_start"):
        mcp_status = "configured"
    mcp_transport = mcp_config.get("default_transport", "stdio")
    mcp_port = mcp_config.get("default_port", 3000)

    # Check VOIP
    voip_status = "stopped"
    if os.getenv("SORA_DOGRAH_WS_URL"):
        voip_status = "configured"

    return {
        "voice": {
            "status": voice_status,
            "type": voice_type,
            "model": voice_model,
            "activeCalls": active_calls,
            "llmProvider": voice_config.get("provider", "gemini-live"),
            "ttsProvider": voice_config.get("tts", {}).get("provider", "edge-tts"),
            "sttProvider": voice_config.get("stt", {}).get("provider", "faster-whisper"),
        },
        "mcp": {
            "status": mcp_status,
            "transport": mcp_transport,
            "port": mcp_port,
            "clients": 0,
        },
        "voip": {
            "status": voip_status,
            "ari": bool(os.getenv("SORA_ARI_URL")),
            "port": 5000,
            "calls": 0,
        },
        "system": {
            "status": "healthy",
            "platform": f"{sys.platform} {sys.version.split()[0]}",
            "python": sys.version.split()[0],
        },
    }


@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """Get dashboard statistics."""
    import psutil
    return {
        "uptime": psutil.boot_time(),
        "memory": psutil.virtual_memory().used,
        "cpu": psutil.cpu_percent(interval=0.1),
        "calls": 0,
    }


@app.get("/api/dashboard/calls")
async def dashboard_calls():
    """Get recent calls."""
    return []


# --- Voice Endpoints ---

@app.get("/api/voice/status")
async def voice_status():
    """Get voice bridge status."""
    config = get_sora_config()
    voice_config = cfg_get(config, "voice", default={})

    return {
        "status": "configured" if voice_config.get("provider") else "stopped",
        "type": voice_config.get("provider", "gemini-live"),
        "model": voice_config.get("gemini_live", {}).get("model", "gemini-2.0-flash-exp"),
        "activeCalls": 0,
        "llmProvider": voice_config.get("provider", "gemini-live"),
        "ttsProvider": voice_config.get("tts", {}).get("provider", "edge-tts"),
        "sttProvider": voice_config.get("stt", {}).get("provider", "faster-whisper"),
        "calls": [],
    }


@app.post("/api/voice/start")
async def voice_start(req: VoiceStartRequest):
    """Start a voice bridge."""
    # This would start the actual bridge
    # For now, just save config
    config = get_sora_config()

    if req.type == "gemini":
        cfg_set(config, "voice", "provider", "gemini-live")
        if req.guildId:
            cfg_set(config, "voice", "gemini_live", "guild_id", req.guildId)
        if req.channelId:
            cfg_set(config, "voice", "gemini_live", "channel_id", req.channelId)
    elif req.type == "vapi":
        cfg_set(config, "voice", "provider", "vapi")
        if req.guildId:
            cfg_set(config, "voice", "vapi", "guild_id", req.guildId)
        if req.channelId:
            cfg_set(config, "voice", "vapi", "channel_id", req.channelId)
        if req.assistantId:
            cfg_set(config, "voice", "vapi", "assistant_id", req.assistantId)
    elif req.type == "elevenlabs":
        cfg_set(config, "voice", "provider", "elevenlabs")
        if req.guildId:
            cfg_set(config, "voice", "elevenlabs", "guild_id", req.guildId)
        if req.channelId:
            cfg_set(config, "voice", "elevenlabs", "channel_id", req.channelId)
        if req.agentId:
            cfg_set(config, "voice", "elevenlabs", "agent_id", req.agentId)
    elif req.type == "voip":
        if req.ariUrl:
            save_env_value("SORA_ARI_URL", req.ariUrl)
        if req.ariUser:
            save_env_value("SORA_ARI_USER", req.ariUser)
        if req.ariPassword:
            save_env_value("SORA_ARI_PASSWORD", req.ariPassword)
        if req.dograhWs:
            save_env_value("SORA_DOGRAH_WS_URL", req.dograhWs)
        cfg_set(config, "voice", "provider", "voip")

    save_sora_config(config)
    return {"status": "started", "type": req.type}


@app.post("/api/voice/stop")
async def voice_stop():
    """Stop voice bridge."""
    config = get_sora_config()
    cfg_set(config, "voice", "provider", "none")
    save_sora_config(config)
    return {"status": "stopped"}


# --- Provider Endpoints ---

@app.post("/api/providers/select")
async def provider_select(req: ProviderSelectRequest):
    """Select active provider for category."""
    config = get_sora_config()

    if req.category == "llm_voice":
        cfg_set(config, "voice", "provider", req.provider)
    elif req.category == "tts":
        cfg_set(config, "voice", "tts", "provider", req.provider)
    elif req.category == "stt":
        cfg_set(config, "voice", "stt", "provider", req.provider)

    save_sora_config(config)
    return {"status": "ok", "category": req.category, "provider": req.provider}


# --- Config Endpoints ---

@app.get("/api/config")
async def get_config():
    """Get full configuration."""
    return get_sora_config()


@app.put("/api/config")
async def update_config(req: ConfigUpdateRequest):
    """Update configuration."""
    save_sora_config(req.config)
    return {"status": "ok"}


@app.get("/api/config/env")
async def get_env():
    """Get environment variables."""
    return get_env_vars()


@app.post("/api/config/env")
async def update_env(req: EnvUpdateRequest):
    """Update environment variables."""
    for key, value in req.env.items():
        if value:
            save_env_value(key, value)
    return {"status": "ok"}


# --- MCP Endpoints ---

@app.get("/api/mcp/status")
async def mcp_status():
    """Get MCP server status."""
    config = get_sora_config()
    mcp_config = cfg_get(config, "mcp", default={})

    return {
        "status": "configured" if mcp_config.get("auto_start") else "stopped",
        "transport": mcp_config.get("default_transport", "stdio"),
        "port": mcp_config.get("default_port", 3000),
    }


@app.get("/api/mcp/servers")
async def mcp_servers():
    """Get configured MCP servers."""
    config = get_sora_config()
    servers = cfg_get(config, "mcp", "servers", default={})
    return list(servers.values())


@app.put("/api/mcp/servers")
async def update_mcp_servers(req: Request):
    """Update MCP servers."""
    body = await req.json()
    config = get_sora_config()
    cfg_set(config, "mcp", "servers", body.get("servers", {}))
    save_sora_config(config)
    return {"status": "ok"}


@app.get("/api/mcp/detect")
async def mcp_detect():
    """Detect MCP servers on system."""
    import psutil

    servers = []
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

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = " ".join(proc.info['cmdline'] or [])
            if 'mcp' in cmdline.lower():
                servers.append({
                    "type": "stdio",
                    "pid": proc.info['pid'],
                    "process": proc.info['name'],
                    "cmdline": cmdline[:100],
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return servers


@app.post("/api/mcp/start")
async def mcp_start(req: McpStartRequest):
    """Start MCP server."""
    config = get_sora_config()
    cfg_set(config, "mcp", "default_transport", req.transport)
    cfg_set(config, "mcp", "default_port", req.port)
    save_sora_config(config)

    # Actually start the server in background
    # This would be handled by the CLI
    return {"status": "starting", "transport": req.transport, "port": req.port}


@app.post("/api/mcp/stop")
async def mcp_stop():
    """Stop MCP server."""
    return {"status": "stopped"}


@app.get("/api/mcp/ws/status")
async def mcp_ws_status():
    """Get WebSocket MCP status."""
    config = get_sora_config()
    ws_config = cfg_get(config, "mcp", "ws", default={})

    return {
        "running": ws_config.get("enabled", False),
        "clients": 0,
    }


@app.post("/api/mcp/ws/start")
async def mcp_ws_start(req: McpWsStartRequest):
    """Start WebSocket MCP server."""
    config = get_sora_config()
    cfg_set(config, "mcp", "ws", "enabled", True)
    cfg_set(config, "mcp", "ws", "host", req.host)
    cfg_set(config, "mcp", "ws", "port", req.port)
    save_sora_config(config)

    return {"status": "starting", "host": req.host, "port": req.port}


@app.post("/api/mcp/ws/stop")
async def mcp_ws_stop():
    """Stop WebSocket MCP server."""
    config = get_sora_config()
    cfg_set(config, "mcp", "ws", "enabled", False)
    save_sora_config(config)
    return {"status": "stopped"}


# --- Main ---

def main():
    """Run the API server."""
    config = get_sora_config()
    network = cfg_get(config, "network", default={})
    http = cfg_get(network, "http", default={})

    host = http.get("host", "0.0.0.0")
    port = http.get("port", 8080)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()