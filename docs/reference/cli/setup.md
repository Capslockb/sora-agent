# sora setup

Interactive setup wizard for S0RA.

## Status

**WORKING**

## Usage

```bash
sora setup                    # Full interactive wizard
sora setup --provider NAME    # Quick-setup a single voice provider
```

## Supported quick-setup providers

```bash
sora setup --provider gemini-live      # Gemini API key
sora setup --provider vapi             # Vapi API key
sora setup --provider elevenlabs       # ElevenLabs API key + Agent ID
sora setup --provider openai-realtime  # OpenAI API key
sora setup --provider xai-grok         # xAI API key
sora setup --provider ultravox         # Ultravox API key
sora setup --provider retell           # Retell API key + Agent ID
```

## What the wizard does

1. Detects existing Hermes/OpenClaw configuration and offers to import.
2. Asks for model provider (OpenRouter, Ollama, etc.).
3. Asks for Discord bot token and default guild/channel.
4. Configures voice bridges (one or many providers).
5. Optionally configures VOIP (Asterisk ARI + Dograh).
6. Configures MCP auto-discovery preferences.
7. Configures memory passthrough (Honcho, Hermes).
8. Enables/disables TTS/STT/LLM-voice providers.
9. Optionally enables OpenWakeWord.

## Verification

```bash
sora setup --provider gemini-live
sora status
```

## Notes

- The wizard writes secrets to `~/.sora/.env` and non-secrets to `~/.sora/config.yaml`.
- It does not start voice bridges; use `sora voice live` or the Hermes plugin after setup.
- Import from `~/.openclaw` is best-effort and **WORKING** for common keys.
