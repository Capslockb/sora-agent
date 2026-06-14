# Ultravox (Managed Pipeline)

## Overview

Ultravox provides a **managed STT → LLM → TTS pipeline** over WebSocket. No audio codec handling needed — Ultravox handles the entire voice conversation pipeline server-side.

## Requirements

| Requirement | Details |
|-------------|---------|
| `ULTRAVOX_API_KEY` | Ultravox API key from console.ultravox.ai |

## Configuration

```bash
sora setup --provider ultravox
# Prompts: ULTRAVOX_API_KEY → model → voice → system prompt
```

Or manually in `~/.sora/config.yaml`:

```yaml
voice:
  ultravox:
    enabled: false
    model: fixie-ai/ultravox
    voice: ""
    system_prompt: ""
```

## Start Bridge

```bash
sora voice ultravox
sora voice ultravox --guild 123... --channel 456...
sora voice ultravox --guild 123... --user 987...
```

## Architecture

```
Create call → Get join URL → WebSocket connect → Stream audio (STT/LLM/TTS handled by Ultravox)
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "ULTRAVOX_API_KEY not set" | `export ULTRAVOX_API_KEY=...` or `sora setup --provider ultravox` |
| Call creation fails | Check API key validity at console.ultravox.ai |
