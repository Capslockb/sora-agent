# Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  S0RA Voice Companion CLI                       │
├─────────────────────────────────────────────────────────────────┤
│  Constants  │  Config  │  Logging  │  Profiles  │  Skins  │     │
├─────────────────────────────────────────────────────────────────┤
│                    Plugin Manager                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ sora-hermes  │  │  sora-voip   │  │      built-in        │  │
│  │  (Discord)   │  │ (Asterisk)   │  │  (MCP, Memory, etc)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  Voice Layer  │  MCP Layer  │  Memory Layer  │  Tool Layer    │
└─────────────────────────────────────────────────────────────────┘
```

## Core Modules (compatibility + voice operations)

| Module | Path | Purpose |
|--------|------|---------|
| Constants | `sora_constants/` | Paths, defaults, version |
| Config | `sora_cli/config.py` | YAML + env merge, profiles |
| Logging | `sora_logging/` | Structured, colored, file+stdout |
| Profiles | `sora_cli/profile.py` | Isolated config directories |
| Skins | `sora_cli/skin.py` | Theme engine (YAML + built-in) |
| Plugins | `sora_cli/plugins.py` | Discovery, enable/disable, YAML |

## Voice Architecture

### Discord Voice Bridges (Hermes-facing)

S0RA does **not** contain the live audio path. It registers `sora_voice_*` tools in Hermes and configures the bridge; actual Discord audio is handled by the Hermes `discord-voice` plugin.

```
User / Hermes Agent
       │
       ▼
┌──────────────────┐
│  sora-hermes     │  Plugin
│  sora_voice_*    │  tools
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Hermes           │
│ discord-voice    │  Plugin
│ VoiceLiveBridge  │
│ LiveAudioSource  │
│ VoiceListener    │
└────────┬─────────┘
         │
         ▼
Gemini Live API (WSS)
```

Status: S0RA tooling **WORKING**; live audio **PARTIAL** (requires `discord-voice`).

### VOIP Bridge (Asterisk + Dograh)

```
Asterisk (SIP/RTP)          Dograh/Gemini Live
       │                          │
       ▼                          ▼
┌──────────────────────────────────────────┐
│         sora-voip Plugin                 │
│  ┌──────────┐  ┌─────────┐  ┌──────────┐ │
│  │ ARI      │  │  RTP    │  │ Dograh   │ │
│  │ Client   │◄─┤ Handler │──►│ Client   │ │
│  └──────────┘  └─────────┘  └──────────┘ │
└──────────────────────────────────────────┘
```

Status: **PARTIAL** — plugin and commands exist; needs PBX runtime.

## MCP Layer

- **stdio MCP**: **WORKING** — S0RA can start and report status.
- **Auto-discovery**: **PARTIAL** — scans ports 3000-3010 + stdio processes.
- **WebSocket MCP**: **PLANNED** — native WS server is scaffolding.
- **CLI Management**: `sora mcp start/status/stop/catalog` — **PARTIAL**.

## FastAPI Dashboard / Sidecar

```
User / Browser
       │
       ▼
┌──────────────────┐
│ FastAPI (8080)   │
│ /health          │
│ /api/status      │
│ /api/visualizer/state │
└──────────────────┘
       │
       ▼
S0RA state + config
```

Status: **WORKING**.

## Integration boundaries

| Boundary | S0RA responsibility | External responsibility |
|---|---|---|
| Discord audio | Config + tools | Hermes `discord-voice` plugin |
| Phone audio | Config + ARI commands | Asterisk + Dograh |
| LLM inference | Provider selection | External API endpoints |
| MCP runtime | stdio start/status | Client (Hermes, Claude Desktop, etc.) |

## Key files

| File | Purpose |
|---|---|
| `sora_bootstrap.py` | UTF-8 stdio setup (Windows) |
| `sora_constants.py` | Profile-aware paths |
| `sora_logging.py` | Centralized logging |
| `sora_api.py` | FastAPI dashboard |
| `sora_cli/main.py` | CLI entry point |
| `sora_cli/setup.py` | Interactive wizard |
| `sora_cli/voice.py` | Voice/provider management |
| `sora_cli/mcp.py` | MCP management |
| `plugins/sora_hermes/` | Hermes plugin |
| `plugins/sora_voip/` | VOIP plugin |

Read [`bridge-elements.md`](../bridge-elements.md) for the operator tool surface and API routes.
