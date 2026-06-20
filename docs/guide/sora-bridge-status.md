# SORA Bridge status

This page describes what the SORA bridge code currently does, what is still scaffolding, and which repo to use for live Gemini Discord voice.

It is based on the current `sora_cli/voice.py`, `sora_api.py`, `plugins/sora_hermes/`, `sora_cli/main.py`, `sora_cli/config.py`, `sora_constants.py`, and `pyproject.toml`.

## Plain-language summary

SORA Agent is the new control layer and future bridge home. It already has useful CLI, profile, API, MCP, Hermes-plugin, TUI, and VOIP surfaces.

It is **not yet a complete replacement** for `Capslockb/gemini-live-discord-bridge`.

Use the older Gemini bridge repo when you need the working live Discord/Gemini audio runtime today. Use this repo when you are configuring SORA, using SORA tools, or building the future SORA-owned bridge layer.

## Current source of truth

| Area | Source of truth |
|---|---|
| Working Discord/Gemini voice runtime | `Capslockb/gemini-live-discord-bridge` |
| SORA CLI and command parser | `sora_cli/main.py` |
| Voice command handlers | `sora_cli/voice.py` |
| Configuration defaults/helpers | `sora_cli/config.py`, `sora_constants.py` |
| FastAPI backend | `sora_api.py` |
| Hermes SORA plugin | `plugins/sora_hermes/` |
| Package entrypoints | `pyproject.toml` |
| TUI source | `ui-tui/` |

## What works as a control surface

| Component | Current behavior |
|---|---|
| `sora setup` | Interactive setup/configuration wizard. |
| `sora status` | Component status path. |
| `sora doctor` | Diagnostics path. |
| `sora config` | Config/env helper path. |
| `sora mcp ...` | MCP command surface. |
| `sora-api` | FastAPI backend with health/status/config/voice/MCP endpoints. |
| `sora voice providers ...` | Provider enable/disable/list/config mutations. |
| `sora voice sip/ari/call/hangup/voip-*` | VOIP/Asterisk/Dograh-oriented command surface. |
| `plugins/sora_hermes` | Registers Hermes tools that call the SORA CLI. |

## What is still scaffolded

### `sora voice live`

The `start_gemini_live()` handler currently:

1. loads SORA config;
2. resolves Discord guild/user defaults;
3. requires `guild_id` and `channel_id`;
4. checks `GEMINI_API_KEY` or `GOOGLE_API_KEY`;
5. checks `DISCORD_BOT_TOKEN`;
6. returns a success/status object saying the Gemini Live bridge is starting.

It does **not** currently start the full long-running Discord receive/playback + Gemini WebSocket bridge from the Gemini bridge repo.

### `sora voice vapi`

The `start_vapi()` handler currently checks config/env and returns a start-status object. Treat it as a control path until the durable Vapi runtime is hardened.

### `sora voice elevenlabs`

The `start_elevenlabs()` handler currently checks config/env and returns a start-status object. Treat it as a control path until a durable runtime is connected.

### `sora voice status`

The status handler currently returns:

```json
{
  "status": "ok",
  "bridges": [],
  "message": "No active voice bridges"
}
```

That means there is not yet an active bridge process registry behind it.

### `sora voice leave`

The stop handler returns a stop-status message. Durable process shutdown depends on the future runtime integration.

## API backend reality

`sora-api` exposes a FastAPI server. The important groups are:

- `/health`
- `/api/status`
- `/api/dashboard/stats`
- `/api/dashboard/calls`
- `/api/voice/status`
- `/api/voice/start`
- `/api/voice/stop`
- `/api/providers/select`
- `/api/config`
- `/api/config/env`
- `/api/mcp/status`
- `/api/mcp/servers`
- `/api/mcp/detect`
- `/api/mcp/start`
- `/api/mcp/stop`
- `/api/mcp/ws/status`
- `/api/mcp/ws/start`
- `/api/mcp/ws/stop`

Important: `/api/voice/start` saves intended provider/config and returns a status response. It does not currently launch a long-running Gemini/Vapi/ElevenLabs bridge process.

`/api/mcp/start` and `/api/mcp/ws/start` also save intended config and return `starting`; process lifecycle still belongs to CLI/runtime work.

## Hermes plugin reality

`plugins/sora_hermes` registers these tools:

- `sora_voice_live`
- `sora_voice_vapi`
- `sora_voice_leave`
- `sora_voice_status`
- `sora_mcp_start`
- `sora_mcp_status`

The tool handlers call the SORA CLI through a subprocess. Because the underlying SORA voice live/vapi commands are still scaffold/control paths, the Hermes tools are not yet production voice runtime launchers.

The plugin also registers slash commands:

- `sora-voice-live`
- `sora-voice-vapi`

Those slash handlers currently return guidance telling users to use the older dedicated Discord voice plugins.

## Correct user flows today

### I want working live Gemini voice in Discord

Use the Gemini bridge repo:

```bash
git clone https://github.com/Capslockb/gemini-live-discord-bridge.git
cd gemini-live-discord-bridge
./install.sh
systemctl --user restart hermes-gateway
```

Then in Discord:

```text
/voice-live
```

### I want to configure SORA or use the SORA control layer

Use this repo:

```bash
pipx install git+https://github.com/Capslockb/sora-agent
sora setup
sora status
sora doctor
sora-api
```

### I want to work on the migration

Use this repo for provider registry, config, API/TUI, Hermes tool surface, MCP, and VOIP work. Use `gemini-live-discord-bridge` as the implementation reference for the current production Gemini Live Discord runtime.

## Migration target

The expected end state is:

1. SORA owns provider selection and config.
2. SORA owns API/TUI controls.
3. SORA owns Hermes tool integration.
4. The working Gemini Discord voice runtime is transplanted or cleanly wrapped.
5. The older Gemini bridge repo becomes either a stable runtime package, compatibility shim, or retired documentation reference.

Until step 4 is done, docs must keep saying that `gemini-live-discord-bridge` is the working live runtime.
