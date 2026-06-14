# ElevenLabs (Discord)

## Overview

[ElevenLabs](https://elevenlabs.io) Conversational AI / ElevenAgents provides a real-time WebSocket API for agent conversations. S0RA uses it as another voice-provider target for Discord voice bridge flows.

The official WebSocket endpoint is:

```text
wss://api.elevenlabs.io/v1/convai/conversation?agent_id=<agent-id>
```

For public agents, `agent_id` is enough. For private agents, S0RA can request a signed URL using `ELEVENLABS_API_KEY` and the official signed-URL endpoint.

## Requirements

| Requirement | Details |
|-------------|---------|
| `ELEVENLABS_AGENT_ID` or `voice.elevenlabs.agent_id` | ElevenLabs Conversational AI agent ID |
| `DISCORD_BOT_TOKEN` | Bot with Voice intents |
| `ELEVENLABS_API_KEY` | Optional for public agents; required for private/signed conversations |

## Configuration

```yaml
voice:
  elevenlabs:
    enabled: true
    agent_id: "your-agent-id"
    channel_id: "optional-provider-specific-discord-channel"
  discord:
    guild_id: "..."
    voice_channel_id: "..."
    default_user_id: "..."
```

The CLI autodetect order for `guild`, `channel`, and `user` is:

1. explicit CLI flags (`--guild`, `--channel`, `--user`)
2. provider config (`voice.elevenlabs.channel_id`, etc.)
3. global Discord config (`voice.discord.guild_id`, `voice.discord.voice_channel_id`, `voice.discord.default_user_id`)
4. environment variables (`DISCORD_GUILD_ID`, `DISCORD_VOICE_CHANNEL_ID`, `DISCORD_USER_ID`)

## Start Bridge

```bash
sora voice elevenlabs
# or explicit target
sora voice elevenlabs --guild <ID> --channel <ID> --user <ID>
```

The command prepares the correct ElevenLabs WebSocket target and reports the protocol contract:

- client audio: `{ "user_audio_chunk": "<base64 pcm chunk>" }`
- server audio: `type="audio"`, `audio_event.audio_base_64`
- ping: respond with `{ "type": "pong", "event_id": <ping_event.event_id> }`

## Agent Setup

1. Create a Conversational AI agent at ElevenLabs.
2. Configure its LLM, tools, and voice in ElevenLabs.
3. Copy the `agent_id` to `voice.elevenlabs.agent_id` or `ELEVENLABS_AGENT_ID`.
4. If the agent is private, set `ELEVENLABS_API_KEY` so S0RA can fetch a signed WebSocket URL.

## Sources

- ElevenLabs WebSocket docs: https://elevenlabs.io/docs/eleven-agents/libraries/web-sockets
- ElevenLabs WebRTC announcement: https://elevenlabs.io/blog/conversational-ai-webrtc
