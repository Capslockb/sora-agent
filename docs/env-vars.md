# Environment Variables

S0RA reads configuration from `~/.sora/config.yaml` and secrets from `~/.sora/.env`. This page is the exhaustive reference grouped by subsystem.

## Required

| Variable | Used by | Status |
|---|---|---|
| `GEMINI_API_KEY` | Gemini Live bridge | Required for Gemini bridge |
| `DISCORD_BOT_TOKEN` | Discord voice bridges | Required for Discord runtime |

## Optional provider keys

| Variable | Used by | Status |
|---|---|---|
| `VAPI_API_KEY` | Vapi.ai bridge | Optional |
| `VAPI_PRIVATE_KEY` | Vapi.ai signing | Optional |
| `ELEVENLABS_API_KEY` | ElevenLabs bridge | Optional |
| `ELEVENLABS_AGENT_ID` | ElevenLabs Conversational AI | Optional |
| `OPENAI_API_KEY` | OpenAI Realtime / TTS / STT | Optional |
| `XAI_API_KEY` | xAI Grok bridge | Optional |
| `ULTRAVOX_API_KEY` | Ultravox bridge | Optional |
| `RETELL_API_KEY` | Retell AI bridge | Optional |

## VOIP

| Variable | Used by | Status |
|---|---|---|
| `SORA_ARI_URL` | Asterisk ARI | Optional |
| `SORA_ARI_USER` | Asterisk ARI auth | Optional |
| `SORA_ARI_PASSWORD` | Asterisk ARI auth | Optional |
| `SORA_DOGRAH_WS_URL` | Dograh gateway | Optional |
| `SORA_DOGRAH_API_KEY` | Dograh auth | Optional |

## Platform integrations

| Variable | Used by | Status |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram notifications | Optional |
| `TELEGRAM_CHAT_ID` | Telegram target chat | Optional |
| `GITHUB_TOKEN` | GitHub tools | Optional |
| `HONCHO_API_KEY` | Honcho memory | Optional |

## S0RA runtime

| Variable | Used by | Default |
|---|---|---|
| `SORA_HOME` | Profile root | `~/.sora` |
| `SORA_API_PORT` | FastAPI dashboard | `8080` |
| `SORA_LOG_LEVEL` | Logging | `INFO` |
| `SORA_PROFILE` | Active profile | `default` |

## Hermes passthrough

When running inside Hermes, S0RA may read:

| Variable | Used by |
|---|---|
| `HERMES_HOME` | Locate Hermes config/plugins |
| `HERMES_PROFILE` | Active Hermes profile |

## Notes

- All secrets belong in `~/.sora/.env`, never in `config.yaml`.
- S0RA does not create `.env` automatically during `sora setup`; the wizard prompts for values and writes them.
- The dashboard endpoint `/api/env` returns key names only, never values.
