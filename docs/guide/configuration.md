# Configuration

## Config File Locations

| Profile | Config Path |
|---------|-------------|
| Default | `~/.sora/config.yaml` |
| Named | `~/.sora-profiles/<name>/config.yaml` |
| Project | `.sora/config.yaml` (via `SORA_HOME`) |

## Config Structure

```yaml
# ~/.sora/config.yaml
display:
  interface: cli        # cli | tui
  skin: sora            # sora | sora-dark | minimal | hermes | <custom>
  theme: dark           # auto | light | dark

model:
  provider: openrouter  # openrouter | ollama | anthropic | openai
  model: anthropic/claude-3.5-sonnet
  temperature: 0.7

voice:
  # Discord Voice Bridges
  gemini_live:
    enabled: true
    model: gemini-3.1-flash-live-preview
    voice: Kore
  vapi:
    enabled: false
    assistant_id: ""
  elevenlabs:
    enabled: false
  
  # Provider Toggle (TTS/STT/LLM Voice)
  providers:
    gemini_live:  { enabled: true,  type: llm_voice }
    vapi:         { enabled: false, type: voice_platform }
    elevenlabs:   { enabled: false, type: tts }
    edge_tts:     { enabled: true,  type: tts }
    openai_tts:   { enabled: false, type: tts }
    whisper:      { enabled: false, type: stt }

  # Discord config
  discord:
    guild_id: ""
    default_user_id: ""

# VOIP / Asterisk + Dograh
voip:
  asterisk_ari_url: "http://localhost:8088/ari"
  asterisk_username: "sora"
  asterisk_password: ""
  asterisk_app_name: "sora-bridge"
  dograh_ws_url: "wss://dograh.local/ws"
  dograh_api_key: ""
  gemini_model: "gemini-2.0-flash-exp"
  sample_rate: 48000
  rtp_port_range: "10000-20000"
  auto_answer: true
  record_calls: false
  recording_dir: "~/.sora/recordings"

mcp:
  enabled: true
  servers: {}
  auto_discover: true
  ws_port: 3000

memory:
  honcho:
    enabled: true
    auto_detect: true
  openclaw:
    enabled: false
    auto_detect: true

plugins:
  enabled: ["sora-voip", "sora-hermes"]

tools:
  opencode:
    enabled: true
    auto_detect: true
  codex:
    enabled: true
  gemini_harness:
    enabled: false

openwakeword:
  enabled: false
  model_path: "~/.sora/openwakeword/hey_sora.onnx"
```

## Environment Variables

| Variable | Description | Required For |
|----------|-------------|--------------|
| `GEMINI_API_KEY` \| `GOOGLE_API_KEY` | Google AI Studio key | Gemini Live |
| `DISCORD_BOT_TOKEN` | Discord bot token | All Discord voice |
| `VAPI_API_KEY` | Vapi.ai API key | Vapi bridge |
| `ELEVENLABS_API_KEY` | ElevenLabs API key | ElevenLabs bridge |
| `OPENAI_API_KEY` | OpenAI API key | OpenAI TTS |
| `OPENROUTER_API_KEY` | OpenRouter key | Model provider |
| `HONCHO_API_KEY` | Honcho memory key | Cloud memory |

## Profiles

```bash
# List profiles
sora config profiles

# Create new profile
sora config profile create my-profile

# Switch profile
sora --profile my-profile

# Or set env var
export SORA_HOME=~/.sora-my-profile
```
