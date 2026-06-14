# Environment Variables

All secrets should be in `.env` or shell environment.

## Required

| Variable | Used For |
|----------|----------|
| `GEMINI_API_KEY` \| `GOOGLE_API_KEY` | Gemini Live (Discord + VOIP) |
| `DISCORD_BOT_TOKEN` | All Discord voice bridges |
| `VAPI_API_KEY` | Vapi.ai bridge |
| `ELEVENLABS_API_KEY` | ElevenLabs bridge |

## Optional

| Variable | Used For |
|----------|----------|
| `OPENAI_API_KEY` | OpenAI TTS, OpenAI models |
| `OPENROUTER_API_KEY` | OpenRouter models |
| `ANTHROPIC_API_KEY` | Anthropic models |
| `OLLAMA_HOST` | Local Ollama (default: http://localhost:11434) |
| `HONCHO_API_KEY` | Honcho cloud memory |
| `HONCHO_WS_URL` | Self-hosted Honcho WS |

## VOIP Specific

| Variable | Used For |
|----------|----------|
| `ASTERISK_ARI_URL` | Override `voip.asterisk_ari_url` |
| `ASTERISK_PASSWORD` | Override `voip.asterisk_password` |
| `DOGRAH_WS_URL` | Override `voip.dograh_ws_url` |
| `DOGRAH_API_KEY` | Override `voip.dograh_api_key` |

## File Locations

```bash
# Default profile
~/.sora/.env

# Named profile
~/.sora-profiles/work/.env

# Project local
.sora/.env (via SORA_HOME)
```

## Loading Priority

1. System environment
2. `~/.sora/.env` (default profile)
3. `~/.sora-profiles/<active>/.env` (named profile)
4. Project `.env` (if `SORA_HOME` set)
