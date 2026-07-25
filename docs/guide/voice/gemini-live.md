# Gemini Live (Discord)

## Status

**PARTIAL** — S0RA configures and prepares the bridge; the live Discord audio runtime is provided by the Hermes `discord-voice` plugin.

## Overview

Direct streaming to Google's **Gemini Live API** via Discord voice channels. Low-latency, multimodal, supports audio + video frames.

## Requirements

| Requirement | Details |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio key |
| `DISCORD_BOT_TOKEN` | Bot with `Voice` + `GuildVoiceStates` intents |
| Hermes `discord-voice` plugin | Installed and enabled in Hermes |
| Discord Bot | Must be in target guild |

## Configuration

```bash
sora setup
# Section: Voice Bridges → Gemini Live
```

Or manually in `~/.sora/config.yaml`:

```yaml
voice:
  gemini_live:
    enabled: true
    model: gemini-2.0-flash-exp
  discord:
    guild_id: "123456789012345678"
    default_user_id: "987654321098765432"
```

## Start bridge

```bash
# From config
sora voice live

# Explicit
sora voice live --guild 123... --channel 456...
```

This command delegates the live connection to the Hermes `discord-voice` plugin.

## Web dashboard

```bash
sora dashboard start --host 127.0.0.1 --port 3000 --api-port 8080
# UI preview: http://127.0.0.1:3000
# Voice status API: http://127.0.0.1:8080/api/status
```

`--port` controls the UI preview and `--api-port` controls the FastAPI control API; do not assign the same port to both. `--host` currently constrains only the API server. The UI preview is launched separately through `npx serve`, and the CLI does not forward an explicit UI bind host.

The control API is unauthenticated and can expose or mutate sensitive configuration. Use the dashboard only on a trusted local machine, and do not publish either listener through a LAN, tunnel, container port, reverse proxy, or the public internet while [Issue #13](https://github.com/Capslockb/sora-agent/issues/13) remains open.

## Troubleshooting

| Issue | Fix |
|---|---|
| "GEMINI_API_KEY not set" | `export GEMINI_API_KEY=***` or add to `~/.sora/.env` |
| "DISCORD_BOT_TOKEN not set" | Same |
| `discord-voice` not found | `hermes plugins enable discord-voice` |
| Bot joins but no audio | Check Discord Voice intents in Developer Portal |
| Green ring but no sound | Check Hermes `discord-voice` `LiveAudioSource` buffer |
| High latency on first connect | Discord CDN quirk: first handshakes may retry. Don't restart repeatedly. |

## Status label reminder

- **WORKING** in S0RA: provider enable/disable, config validation, status API.
- **PARTIAL** for live audio: depends on Hermes `discord-voice` runtime.
