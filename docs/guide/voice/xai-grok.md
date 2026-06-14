# xAI Grok (WSS)

## Overview

xAI's **Grok Realtime API** over WebSocket with PCM 16kHz mono audio. Simple raw WebSocket transport with x-api-key auth.

## Requirements

| Requirement | Details |
|-------------|---------|
| `XAI_API_KEY` | xAI API key from console.x.ai |

## Configuration

```bash
sora setup --provider xai-grok
# Prompts: XAI_API_KEY → model → voice → instructions
```

Or manually in `~/.sora/config.yaml`:

```yaml
voice:
  xai_grok:
    enabled: false
    model: grok-realtime
    voice: ""
    instructions: ""
```

## Start Bridge

```bash
sora voice xai
sora voice xai --guild 123... --channel 456...
sora voice xai --guild 123... --user 987...
```

## Audio Format

- PCM 16kHz mono, 16-bit signed integer
- Raw WSS transport (no WebRTC)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "XAI_API_KEY not set" | `export XAI_API_KEY=...` or `sora setup --provider xai-grok` |
| WSS connection fails | Check connectivity to xAI endpoint |
