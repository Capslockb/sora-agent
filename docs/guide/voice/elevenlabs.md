# ElevenLabs (Discord)

## Overview

[ElevenLabs](https://elevenlabs.io) Conversational AI + high-quality TTS. S0RA bridges Discord voice to ElevenLabs.

## Requirements

| Requirement | Details |
|-------------|---------|
| `ELEVENLABS_API_KEY` | From [elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys) |
| `DISCORD_BOT_TOKEN` | Bot with Voice intents |
| ElevenLabs Agent | Create at [elevenlabs.io/app/conversational-ai](https://elevenlabs.io/app/conversational-ai) |

## Configuration

```yaml
voice:
  elevenlabs:
    enabled: true
    agent_id: "your-agent-id"
  discord:
    guild_id: "..."
    default_user_id: "..."
```

## Start Bridge

```bash
sora voice elevenlabs
```

## Agent Setup

1. Create Conversational AI agent at ElevenLabs
2. Configure LLM (GPT-4, Claude, etc.)
3. Choose voice from library
4. Copy `agent_id` to config

## Voice Library

ElevenLabs offers 1000+ voices. Use voice IDs like:
- `21m00Tcm4TlvDq8ikWAM` (Rachel)
- `AZnzlk1XvdvUeBnXmlld` (Domi)
- `EXAVITQu4vr4xnSDxMaL` (Bella)
