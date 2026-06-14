# Gemini Live (Discord)

## Overview

Direct streaming to Google's **Gemini Live API** via Discord voice channels. Low-latency, multimodal, supports audio + video frames.

## Requirements

| Requirement | Details |
|-------------|---------|
| `GEMINI_API_KEY` | Google AI Studio key |
| `DISCORD_BOT_TOKEN` | Bot with `Voice` + `GuildVoiceStates` intents |
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
    model: gemini-3.1-flash-live-preview
    voice: Kore  # Kore, Puck, Charon, Aoede, Fenrir, Leda, Orus, Zephyr
  discord:
    guild_id: "123456789012345678"
    default_user_id: "987654321098765432"
```

## Start Bridge

```bash
# Auto from config
sora voice live

# Explicit
sora voice live --guild 123... --channel 456...

# With user inference
sora voice live --guild 123... --user 987...
```

## Voice Selection

| Voice | Style |
|-------|-------|
| Kore | Firm, professional |
| Puck | Upbeat, energetic |
| Charon | Deep, authoritative |
| Aoede | Warm, melodic |
| Fenrir | Gruff, distinct |
| Leda | Soft, gentle |
| Orus | Clear, articulate |
| Zephyr | Light, airy |

## Web Dashboard

```bash
sora dashboard start
# Open http://localhost:3000
# Navigate to Voice → Gemini Live
# See live connection status, latency, transcripts
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "GEMINI_API_KEY not set" | `export GEMINI_API_KEY=*** or add to `.env` |
| "DISCORD_BOT_TOKEN not set" | Same |
| Bot joins but no audio | Check Discord Voice intents in Developer Portal |
| Green ring but no sound | Check `LiveAudioSource` buffer, try `sora voice leave` + restart |
| High latency | Discord CDN quirk: first 5 handshakes fail (~27s). **Don't restart repeatedly** — let it complete. |
