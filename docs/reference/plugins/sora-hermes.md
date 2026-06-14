# sora-hermes Plugin

Discord voice bridges for S0RA.

## Features

- **Gemini Live** — Direct to Google's multimodal API
- **Vapi.ai** — Bridge to Vapi assistants
- **ElevenLabs** — Bridge to ElevenLabs Conversational AI

## Installation

```bash
# Built into S0RA — no separate install needed
sora plugins enable sora-hermes
```

## Configuration

```yaml
voice:
  gemini_live:
    enabled: true
    model: gemini-3.1-flash-live-preview
    voice: Kore
  vapi:
    enabled: false
    assistant_id: ""
  elevenlabs:
    enabled: false
    agent_id: ""
  discord:
    guild_id: "123..."
    default_user_id: "987..."
```

## Commands

```bash
sora voice live      # Start Gemini Live
sora voice vapi      # Start Vapi
sora voice elevenlabs # Start ElevenLabs
sora voice status    # Check status
sora voice leave     # Stop bridge
```

## Discord Slash Commands

| Command | Description |
|---------|-------------|
| `/voice-live` | Start Gemini Live in current channel |
| `/voice-vapi` | Start Vapi in current channel |
| `/voice-leave` | Stop bridge |
| `/voice-status` | Show status |

## Architecture

```
Discord Gateway (Voice WS)
       │
       ▼
┌─────────────────────────┐
│ bridge.py               │
│  VoiceLiveBridge        │──► Manages connections
│  LiveAudioSource        │──► Discord AudioSource (PCM out)
│  VoiceListener          │──► Receives Opus, decodes to PCM
│  GeminiLiveSession      │──► WSS to Gemini Live API
└─────────────────────────┘
```