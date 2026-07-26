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

- **Built-in stdio server**: **WORKING** — `sora mcp start --transport stdio` reaches the checked-in foreground server implementation.
- **Status and discovery**: **PARTIAL** — `sora mcp status` combines saved configuration with process-name and listening-port heuristics. It does not perform an MCP handshake or prove protocol health, and unrelated processes can be reported as MCP servers.
- **SSE and streamable HTTP**: **PLANNED** — the CLI accepts both transport names, but the server raises `NotImplementedError` for them.
- **Raw WebSocket listener**: **PARTIAL — UNSAFE** — `sora mcp ws start` is separate from the implemented stdio server, defaults to `0.0.0.0:3001`, has no authentication, and its tool-call path is incomplete.
- **CLI management**: **PARTIAL** — the registered top-level commands are `start`, `status`, `list`, `catalog`, `add`, `remove`, `enable`, and `disable`, plus `ws start/stop/status/list`. The `ws stop/status/list` commands are stubs, and there is no top-level `sora mcp stop` command.

Do not expose the WebSocket listener or treat heuristic status output as runtime validation. See [Issue #16](https://github.com/Capslockb/sora-agent/issues/16).

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

- `sora dashboard start` defaults the API to `0.0.0.0:8080`;
- `--host` is forwarded to the API server only, while the UI preview is launched separately without an explicit bind-host argument;
- sensitive read and mutation routes have no authentication or authorization;
- CORS permits all origins, methods, and headers;
- configuration endpoints can return or modify stored configuration and environment values, including credentials.

The command below constrains the API listener only; it does not prove that the separately launched UI preview is loopback-bound:

```bash
sora dashboard start --host 127.0.0.1 --port 3000 --api-port 8080
```

Until [Issue #13](https://github.com/Capslockb/sora-agent/issues/13) is resolved, run the dashboard only on a trusted local machine. Do not publish either listener through a LAN, public tunnel, reverse proxy, Tailscale Serve/Funnel, or a container port.

## Integration boundaries

| Boundary | S0RA responsibility | External responsibility |
|---|---|---|
| Discord audio | Config + tools | Hermes `discord-voice` plugin |
| Phone audio | Intended config, ARI, RTP, and Dograh components; startup remains blocked by Issue #14 | Asterisk + Dograh after the local construction path is repaired |
| LLM inference | Provider selection | External API endpoints |
| MCP runtime | stdio start/status | Client (Hermes, Claude Desktop, etc.) |
| Dashboard control API | Local UI, status, and configuration control | Operator must constrain the API listener, avoid shared/network-reachable hosts, and not publish either dashboard listener until authentication, redaction, and UI bind control are implemented |

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
