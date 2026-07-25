# SORA Bridge status

This page describes what the SORA bridge code currently does, what remains a control or preparation path, and which repository provides the live Gemini Discord voice runtime.

It is grounded in the current `sora_cli/voice.py`, provider client modules, `sora_api.py`, `plugins/sora_hermes/`, `sora_cli/main.py`, `sora_cli/config.py`, `sora_constants.py`, and `pyproject.toml`.

## Plain-language summary

SORA Agent is a multi-provider control layer and future bridge home. It already has useful CLI, profile, API, MCP, Hermes-plugin, TUI, provider-preparation, and VOIP surfaces.

It is **not yet a complete standalone replacement** for `Capslockb/gemini-live-discord-bridge` or the Hermes `discord-voice` runtime.

Use the Gemini bridge repository when you need the currently documented live Discord/Gemini audio loop. Use this repository when configuring SORA, exercising provider preparation paths, using SORA tools, or building the future SORA-owned media bridge.

## Current source of truth

| Area | Source of truth |
|---|---|
| Working Discord/Gemini voice runtime | `Capslockb/gemini-live-discord-bridge` and Hermes `discord-voice` |
| SORA CLI and command parser | `sora_cli/main.py` |
| Voice command handlers | `sora_cli/voice.py` |
| Provider-specific preparation/API clients | `sora_cli/*_client.py` |
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
| `sora voice live/vapi/elevenlabs/openai/xai/ultravox/retell` | Provider validation or preparation paths; behavior differs by provider and does not itself prove a durable Discord media bridge. |
| `sora voice sip/ari/call/hangup/voip-*` | VOIP/Asterisk/Dograh-oriented command surface. |
| `plugins/sora_hermes` | Registers Hermes tools that call the SORA CLI. |

## Provider command reality

### `sora voice live`

The Gemini handler currently:

1. loads SORA config;
2. resolves Discord guild/user/channel defaults;
3. requires `guild_id` and `channel_id`;
4. checks `GEMINI_API_KEY` or `GOOGLE_API_KEY`;
5. checks `DISCORD_BOT_TOKEN`;
6. checks the `discord-voice` plugin flag and required Python voice dependencies;
7. returns a structured **prerequisites verified** result.

It does **not** start the long-running Discord receive/playback and Gemini WebSocket loop by itself.

### `sora voice vapi`

The Vapi handler checks Discord targeting, `VAPI_API_KEY`, and `DISCORD_BOT_TOKEN`, then returns a start-status object. It does not create or supervise a durable Discord media session.

### `sora voice elevenlabs`

The ElevenLabs handler:

- resolves Discord targeting;
- requires an agent ID and Discord token;
- uses a public conversation URL or requests a signed URL when an API key is available;
- returns redacted WebSocket target and protocol metadata.

This is useful bridge preparation, but the handler does not run the Discord audio capture/playback loop.

### `sora voice openai`

The OpenAI Realtime handler creates a provider client, connects briefly to obtain an ephemeral key, disconnects, and returns a redacted readiness result. It does not keep a Realtime session alive or bridge Discord audio.

### `sora voice xai`

The xAI handler validates the API key, builds provider configuration, instantiates the client, and reports readiness. It does not connect a persistent voice stream or bridge Discord media.

### `sora voice ultravox`

The Ultravox handler creates a provider-side call and returns a shortened join URL. It does not connect that call to Discord audio or supervise its lifecycle.

### `sora voice retell`

The Retell handler creates a provider-side web call and returns its call ID. It does not connect the call to Discord audio or supervise the media lifecycle.

### `sora voice status`

The status handler currently returns:

```json
{
  "status": "ok",
  "bridges": [],
  "message": "No active voice bridges"
}
```

There is no active bridge-process registry behind this response yet.

### `sora voice leave`

The stop handler returns a stop-status message. Durable process shutdown depends on future runtime integration.

## API backend reality

`sora-api` exposes a FastAPI server. Important route groups include:

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

Important: `/api/voice/start` saves intended provider/config and returns a status response. It does not prove that a long-running provider-to-Discord media process started.

`/api/mcp/start` and `/api/mcp/ws/start` also save intended config and return `starting`; process lifecycle still belongs to CLI/runtime work.

## Hermes plugin reality

`plugins/sora_hermes` registers these tools:

- `sora_voice_live`
- `sora_voice_vapi`
- `sora_voice_leave`
- `sora_voice_status`
- `sora_mcp_start`
- `sora_mcp_status`

The tool handlers call the SORA CLI through a subprocess. Because the underlying live and Vapi commands are still validation/control paths, these tools are not standalone production voice-runtime launchers.

The plugin also registers slash commands:

- `sora-voice-live`
- `sora-voice-vapi`

Those slash handlers currently direct users toward the dedicated Discord voice plugins.

## Correct user flows today

### I want working live Gemini voice in Discord

Use the Gemini bridge repository:

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

### I want to configure SORA or inspect provider preparation

Use this repository:

```bash
pipx install git+https://github.com/Capslockb/sora-agent
sora setup
sora status
sora doctor
sora voice providers list
sora-api
```

Provider commands may validate credentials, prepare provider resources, or return provider-side identifiers. Do not treat a successful CLI response as proof of a live Discord audio bridge unless the media runtime is separately observed.

### I want to work on the migration

Use this repository for provider registry, config, API/TUI, Hermes tool surface, MCP, provider clients, and VOIP work. Use `gemini-live-discord-bridge` as the implementation reference for the current live Gemini Discord runtime.

## Validation boundary

The last recorded local pytest result was 24/24 on PR #5. The staged workflow is not active, so current `main` and pull requests are not automatically pytest-verified. See Issue #12.

Security-sensitive CLI and deterministic-build remediation remains tracked in Issue #7. Documentation must not present those findings as resolved until an exact-head fix is reviewed and tested.

## Migration target

The expected end state is:

1. SORA owns provider selection and config.
2. SORA owns API/TUI controls.
3. SORA owns Hermes tool integration.
4. SORA owns a durable media-session registry and lifecycle.
5. Provider preparation paths connect to a tested Discord capture/playback bridge.
6. The older Gemini bridge repository becomes a stable runtime package, compatibility shim, or retired documentation reference.

Until steps 4 and 5 are complete, documentation must distinguish provider-side readiness from an active Discord voice bridge.