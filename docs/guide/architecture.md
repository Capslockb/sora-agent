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

The diagram below describes the intended data path, not a currently runnable startup path.

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

Status: **PARTIAL — STARTUP BLOCKED**. The component classes and management commands exist, but both checked-in VOIP entrypoints fail during local configuration and bridge construction before they reach Asterisk or Dograh. Supplying a PBX and credentials is not sufficient. See [Issue #14](https://github.com/Capslockb/sora-agent/issues/14).

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
┌────────────────────────────┐
│ FastAPI control API (8080) │
│ /health                    │
│ /api/status                │
│ /api/config                │
│ /api/config/env            │
│ voice/provider/MCP routes  │
└─────────────┬──────────────┘
              │
              ▼
       S0RA state + config
```

Status: **PARTIAL**. The dashboard and routes run, but the current control surface is not safe for network exposure:

- `sora dashboard start` defaults to `0.0.0.0:8080`;
- sensitive read and mutation routes have no authentication or authorization;
- CORS permits all origins, methods, and headers;
- configuration endpoints can return or modify stored configuration and environment values, including credentials.

Until [Issue #13](https://github.com/Capslockb/sora-agent/issues/13) is resolved, start it explicitly on loopback:

```bash
sora dashboard start --host 127.0.0.1 --api-port 8080
```

Do not expose the listener to a LAN, public tunnel, published container interface, or the internet.

## Integration boundaries

| Boundary | S0RA responsibility | External responsibility |
|---|---|---|
| Discord audio | Config + tools | Hermes `discord-voice` plugin |
| Phone audio | Intended config, ARI, RTP, and Dograh components; startup remains blocked by Issue #14 | Asterisk + Dograh after the local construction path is repaired |
| LLM inference | Provider selection | External API endpoints |
| MCP runtime | stdio start/status | Client (Hermes, Claude Desktop, etc.) |
| Dashboard control API | Local UI, status, and configuration control | Operator must keep the listener loopback-only until authentication and redaction are implemented |

## Key files

| File | Purpose |
|---|---|
| `sora_bootstrap.py` | UTF-8 stdio setup (Windows) |
| `sora_constants.py` | Profile-aware paths |
| `sora_logging.py` | Centralized logging |
| `sora_api.py` | FastAPI dashboard and control API |
| `sora_cli/main.py` | CLI entry point |
| `sora_cli/setup.py` | Interactive wizard |
| `sora_cli/voice.py` | Voice/provider management |
| `sora_cli/mcp.py` | MCP management |
| `plugins/sora_hermes/` | Hermes plugin |
| `plugins/sora_voip/` | VOIP plugin |

Read [`bridge-elements.md`](../bridge-elements.md) for the operator tool surface and API routes.
