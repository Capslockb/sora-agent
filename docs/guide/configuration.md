# Configuration

SORA uses profile-aware configuration. The active home directory is controlled by `SORA_HOME`; when unset, SORA uses `~/.sora/`.

## File locations

| Purpose | Path |
|---|---|
| Default SORA home | `~/.sora/` |
| Main config | `~/.sora/config.yaml` |
| Env file | `~/.sora/.env` |
| Logs | `~/.sora/logs/` |
| Sessions | `~/.sora/sessions/` |
| Plugins | `~/.sora/plugins/` |
| Skills | `~/.sora/skills/` |
| Cron jobs | `~/.sora/cron/` |
| Named profile | `~/.sora/profiles/<name>/` if it exists |
| Alternate named profile | `~/.sora-<name>/` if it exists |
| Project/custom home | any path via `SORA_HOME=/path/to/home` |

Important correction: named profiles are resolved as `~/.sora/profiles/<name>/` or `~/.sora-<name>/`, not `~/.sora-profiles/<name>/`.

## Profile usage

```bash
# Use default profile
sora --profile default status

# Use an existing named profile
sora --profile myprofile setup

# Or set an explicit home
export SORA_HOME=~/.sora-myprofile
sora status
```

Profile names must match the validation in `sora_cli/main.py`: lowercase letters/numbers plus `_` or `-`, starting with a letter/number.

## Default config shape

The current defaults are defined in `sora_cli/config.py`. Useful sections include:

```yaml
model:
  provider: openrouter
  base_url: https://openrouter.ai/api/v1
  default: nvidia/nemotron-3-ultra:free
  reasoning_effort: medium

display:
  interface: cli
  skin: sora
  show_tool_progress: true
  show_reasoning: true
  context_bar: true

memory:
  provider: honcho
  honcho:
    host: http://localhost:8377
    peer: user

voice:
  gemini_live:
    enabled: true
    model: gemini-3.1-flash-live-preview
    voice: Kore
    auto_greeting: "I'm here."
    allowed_speakers: []
    video_enabled: true
    video_max_fps: 1.0
    audio_preroll_ms: 320
    auto_leave_quiet_seconds: 900
  vapi:
    enabled: true
    assistant_id: ""
    phone_number_id: ""
  discord:
    bot_token: ""
    application_id: ""
    guild_id: ""
    default_user_id: ""
    voice_channel_id: ""

mcp:
  enabled: true
  servers: {}
```

The loaded config is a deep merge of these defaults and the user's `config.yaml`.

## Environment variables

Common keys read by CLI/API paths:

| Variable | Used for |
|---|---|
| `OPENROUTER_API_KEY` | Default model provider path |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Gemini and Gemini Live config checks |
| `VAPI_API_KEY` | Vapi config checks |
| `ELEVENLABS_API_KEY` | ElevenLabs config checks |
| `DISCORD_BOT_TOKEN` | Discord voice command prerequisite checks |
| `DISCORD_APPLICATION_ID` | Discord/Hermes integration settings |
| `HONCHO_API_KEY` | Honcho/cloud memory integration |
| `SORA_ARI_URL` | Asterisk ARI integration |
| `SORA_ARI_USER` | Asterisk ARI username |
| `SORA_ARI_PASSWORD` | Asterisk ARI password |
| `SORA_DOGRAH_WS_URL` | Dograh WebSocket URL |
| `SORA_DOGRAH_API_KEY` | Dograh API key |
| `SORA_HOME` | Override active SORA home/profile |
| `SORA_TUI` | Force TUI startup when set to `1` |
| `SORA_REDACT_SECRETS` | Secret-redaction behavior |
| `SORA_FORCE_IPV4` | IPv4 preference flag |

The API exposes env read/update helpers at:

```text
GET  /api/config/env
POST /api/config/env
```

## Voice configuration caveat

The config contains Gemini Live, Vapi, ElevenLabs, and Discord settings. These are useful for SORA's future bridge ownership, but the current `sora voice live`, `sora voice vapi`, and `sora voice elevenlabs` handlers still behave as control/scaffold paths.

They validate env/config and return status. They do not yet launch the complete long-running runtime that exists in `gemini-live-discord-bridge`.

Read: [`sora-bridge-status.md`](sora-bridge-status.md)

## API backend configuration

`sora-api` reads `network.http` from config and falls back to:

```text
host: 0.0.0.0
port: 8080
```

Example config:

```yaml
network:
  http:
    host: 127.0.0.1
    port: 8080
```

## MCP configuration

The API and CLI use the `mcp` section for server configuration, default transport, default port, and WebSocket settings.

API endpoints include:

```text
/api/mcp/status
/api/mcp/servers
/api/mcp/detect
/api/mcp/start
/api/mcp/stop
/api/mcp/ws/status
/api/mcp/ws/start
/api/mcp/ws/stop
```

`/api/mcp/start` and `/api/mcp/ws/start` currently save intended config and return a starting response; verify actual runtime state separately.
