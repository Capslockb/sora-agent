# OpenAI Realtime (WebRTC)

## Overview

OpenAI's **WebRTC-based realtime voice API** with function calling. Low-latency bidirectional audio streaming via `aiortc`.

## Requirements

| Requirement | Details |
|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (platform.openai.com) |
| Python 3.11+ | Required by `aiortc` |

## Configuration

```bash
sora setup --provider openai-realtime
# Prompts: OPENAI_API_KEY → model → voice → instructions
```

Or manually in `~/.sora/config.yaml`:

```yaml
voice:
  openai_realtime:
    enabled: true
    model: gpt-4o-realtime-preview
    voice: alloy  # alloy, echo, fable, nova, onyx, shimmer
    instructions: ""
```

## Start Bridge

```bash
# Auto from config + env
sora voice openai

# Explicit guild/channel
sora voice openai --guild 123... --channel 456...

# With user inference
sora voice openai --guild 123... --user 987...
```

## Voice Selection

| Voice | Style |
|-------|-------|
| alloy | Neutral, balanced |
| ash | Versatile, natural |
| ballad | Warm, musical |
| coral | Bright, energetic |
| echo | Deep, resonant |
| fable | Soft, narrative |
| nova | Clear, articulate |
| onyx | Strong, authoritative |
| sage | Calm, measured |
| shimmer | Light, airy |
| verse | Expressive, dramatic |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "OPENAI_API_KEY not set" | `export OPENAI_API_KEY=...` or `sora setup --provider openai-realtime` |
| aiortc import error | `pip install aiortc` |
