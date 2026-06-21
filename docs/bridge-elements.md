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
| `sora_voice_live` | **PARTIAL** | `guild_id`, `channel_id` | Bridge start request (runtime: Hermes `discord-voice`) |
| `sora_voice_vapi` | **PARTIAL** | `guild_id`, `channel_id` | Bridge start request (runtime: Hermes `discord-voice`) |
| `sora_voice_leave` | **PARTIAL** | `guild_id` | Stop request (runtime: Hermes `discord-voice`) |
| `sora_voice_status` | **WORKING** | — | JSON status from S0RA state |
| `sora_mcp_start` | **PARTIAL** | `transport`, `port` | Start request |
| `sora_mcp_status` | **WORKING** | — | JSON MCP status |

## Sidecar HTTP API

The FastAPI dashboard (`sora_api.py`) exposes local control endpoints. Default port is `8080` and can be changed with `SORA_API_PORT`.

| Method | Path | Status | Description |
|---|---|---|---|
| GET | `/health` | **WORKING** | `{status: "healthy", service: "sora-api"}` |
| GET | `/api/status` | **WORKING** | Voice, MCP, VOIP, and system status |
| GET | `/api/dashboard/stats` | **WORKING** | CPU/memory metrics |
| GET | `/api/dashboard/calls` | **WORKING** | Recent calls (empty until VOIP active) |
| GET | `/api/visualizer/state` | **WORKING** | UI-friendly visualizer snapshot |
| GET | `/api/config` | **WORKING** | Current S0RA config (safe keys) |
| POST | `/api/config` | **WORKING** | Update S0RA config |
| GET | `/api/env` | **WORKING** | Env keys without values (redacted list) |
| POST | `/api/env` | **WORKING** | Update env values |
| POST | `/api/voice/start` | **PARTIAL** | Prepare voice bridge start; depends on external runtime |
| POST | `/api/voice/stop` | **PARTIAL** | Stop voice bridge; depends on external runtime |
| POST | `/api/mcp/start` | **PARTIAL** | Start MCP server; stdio works, HTTP/SSE scaffolded |
| POST | `/api/mcp/stop` | **PARTIAL** | Stop MCP server |

## Integration boundaries

```
User / Hermes Agent
        │
        ├── sora CLI (local process)
        │      ├── setup · voice · mcp · status · doctor
        │      └── FastAPI dashboard (port 8080)
        │
        └── sora-hermes plugin in Hermes gateway
               ├── sora_voice_* tools
               └── sora_mcp_* tools
                        │
                        ▼
              Hermes discord-voice plugin
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

# 2. Sidecar health
curl -s http://127.0.0.1:8080/health | python3 -m json.tool
curl -s http://127.0.0.1:8080/api/status | python3 -m json.tool

# 3. Hermes plugin registration
hermes tools list | grep sora_
```

## Safety contract

- S0RA never sends audio itself; it configures or queries the bridge runtime.
- S0RA never stores plaintext secrets in logs; env values are redacted from `/api/env`.
- S0RA commands fail loudly when a runtime dependency is missing.
