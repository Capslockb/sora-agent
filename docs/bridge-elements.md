# Bridge Elements

S0RA is designed around the same bridge-element philosophy as the Gemini bridge: small, operator-facing surfaces that let users and agents start, stop, inspect, and verify real-time voice systems.

## What is a S0RA bridge element?

A bridge element is any piece of S0RA that:

1. Exposes a clear command or API.
2. Has a verifiable status (`WORKING`, `PARTIAL`, `PLANNED`, `RESEARCH`).
3. Can be driven from the CLI, the HTTP sidecar, or from Hermes via the `sora-hermes` plugin.

## Operator tools (Hermes plugin)

When `plugins/sora_hermes/` is enabled in Hermes, these tools become available to the agent:

| Tool | Status | Input | Output |
|---|---|---|---|
| `sora_voice_live` | **PARTIAL** | `guild_id`, `channel_id`, optional `user_id` | Runs the S0RA Gemini bridge-preparation CLI; live media still depends on the Hermes voice runtime |
| `sora_voice_vapi` | **PARTIAL** | `guild_id`, `channel_id`, optional `user_id` | Runs the S0RA Vapi bridge-preparation CLI; live media still depends on the Hermes voice runtime |
| `sora_voice_leave` | **PARTIAL** | `guild_id` | Runs the S0RA leave command; effective shutdown depends on the external bridge runtime |
| `sora_voice_status` | **WORKING** | — | Returns S0RA's configured voice status |
| `sora_mcp_start` | **PARTIAL** | `transport`, `port` | Runs the MCP start command; non-stdio transports remain scaffolded |
| `sora_mcp_status` | **WORKING** | — | Returns configured MCP status |

## Sidecar HTTP API

The FastAPI dashboard is implemented in `sora_api.py`. Its host and port come from `network.http.host` and `network.http.port`; the current defaults are **`0.0.0.0:8080`**.

> **Security warning:** the current API has no authentication or authorization, enables broad CORS, and includes routes that return or modify configuration and environment values. Do not expose it to a LAN or the internet. Bind it to loopback or block external access until [Issue #13](https://github.com/Capslockb/sora-agent/issues/13) is resolved.

### Status and dashboard routes

| Method | Path | Status | Current behavior |
|---|---|---|---|
| GET | `/health` | **WORKING** | Returns API liveness metadata |
| GET | `/api/status` | **WORKING** | Returns configured voice, MCP, VOIP, and system state |
| GET | `/api/dashboard/stats` | **WORKING** | Returns host CPU, memory, and uptime data |
| GET | `/api/dashboard/calls` | **WORKING** | Returns an empty call list in the current implementation |
| GET | `/api/visualizer/state` | **WORKING** | Returns a synthetic/configuration-derived visualizer snapshot |

### Configuration routes

| Method | Path | Status | Current behavior |
|---|---|---|---|
| GET | `/api/config` | **WORKING — SENSITIVE** | Returns the full stored S0RA configuration without authentication |
| PUT | `/api/config` | **WORKING — SENSITIVE** | Replaces the stored configuration without authentication |
| GET | `/api/config/env` | **WORKING — CRITICAL** | Returns configured environment values, including secrets, without authentication |
| POST | `/api/config/env` | **WORKING — CRITICAL** | Writes supplied environment values without authentication |
| POST | `/api/providers/select` | **WORKING — SENSITIVE** | Changes the configured provider selection |

The older `/api/env` paths and `POST /api/config` method are not implemented.

### Voice and MCP control routes

| Method | Path | Status | Current behavior |
|---|---|---|---|
| GET | `/api/voice/status` | **WORKING** | Returns configuration-derived voice status; it does not prove a live media session |
| POST | `/api/voice/start` | **PARTIAL** | Saves provider and bridge configuration; it does not start the external live-audio runtime |
| POST | `/api/voice/stop` | **PARTIAL** | Clears the configured provider; it does not supervise an external bridge process |
| GET | `/api/mcp/status` | **WORKING** | Returns configuration-derived MCP status |
| GET | `/api/mcp/servers` | **WORKING** | Returns configured MCP server entries |
| PUT | `/api/mcp/servers` | **WORKING — SENSITIVE** | Replaces configured MCP server entries |
| GET | `/api/mcp/detect` | **PARTIAL** | Scans local processes and common ports for possible MCP servers |
| POST | `/api/mcp/start` | **PARTIAL** | Records requested transport and port; it does not launch the server in this route |
| POST | `/api/mcp/stop` | **PARTIAL** | Returns a stopped response without supervising a process |
| GET | `/api/mcp/ws/status` | **PARTIAL** | Returns configuration-derived WebSocket status |
| POST | `/api/mcp/ws/start` | **PARTIAL** | Marks WebSocket MCP enabled in config; it does not start a listener |
| POST | `/api/mcp/ws/stop` | **PARTIAL** | Marks WebSocket MCP disabled in config |

## Integration boundaries

```text
User / Hermes Agent
        │
        ├── sora CLI (local process)
        │      ├── setup · voice · mcp · status · doctor
        │      └── FastAPI dashboard (default 0.0.0.0:8080)
        │
        └── sora-hermes plugin in Hermes gateway
               ├── sora_voice_* tools
               └── sora_mcp_* tools
                        │
                        ▼
              External Hermes voice runtime
              (live Discord audio path)
                        │
                        ▼
              Gemini / Vapi / ElevenLabs / OpenAI / xAI / Ultravox / Retell
```

## Verification commands

```bash
# 1. CLI bridge surface
sora voice status
sora mcp status
sora status --json

# 2. Sidecar health — use loopback only
curl -s http://127.0.0.1:8080/health | python3 -m json.tool
curl -s http://127.0.0.1:8080/api/status | python3 -m json.tool

# 3. Hermes plugin registration
hermes tools list | grep sora_
```

Do not use the sensitive configuration routes as casual smoke tests: the current implementation returns real values and has no access control.

## Safety contract

- S0RA does not implement the live Discord audio loop in this repository; it prepares or queries the external bridge runtime.
- The dashboard API is currently a trusted-local-development surface, not a secured service boundary.
- Secret handling is not yet safe across all CLI and HTTP paths. Track CLI remediation in [Issue #7](https://github.com/Capslockb/sora-agent/issues/7) and API remediation in [Issue #13](https://github.com/Capslockb/sora-agent/issues/13).
- Treat configuration-derived status as configuration state, not proof that an external process or media session is alive.
