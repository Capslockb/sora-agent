# config.yaml Reference

Complete configuration schema.

```yaml
# Display
display:
  interface: cli           # cli | tui
  skin: sora               # sora | sora-dark | minimal | hermes
  theme: auto              # auto | light | dark

# Model
model:
  provider: openrouter     # openrouter | ollama | anthropic | openai
  model: anthropic/claude-3.5-sonnet
  temperature: 0.7
  max_tokens: 4096

# Voice (Discord + VOIP)
voice:
  # Discord Bridges
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

  # Provider Toggle
  providers:
    gemini_live:  { enabled: true,  configured: true,  type: llm_voice }
    vapi:         { enabled: false, configured: false, type: voice_platform }
    elevenlabs:   { enabled: false, configured: false, type: tts }
    edge_tts:     { enabled: true,  configured: true,  type: tts }
    openai_tts:   { enabled: false, configured: false, type: tts }
    whisper:      { enabled: false, configured: false, type: stt }

  # Discord
  discord:
    guild_id: ""
    default_user_id: ""

# VOIP
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

# MCP
mcp:
  enabled: true
  servers: {}
  auto_discover: true
  ws_port: 3000

# Memory
memory:
  honcho:
    enabled: true
    auto_detect: true
  openclaw:
    enabled: false
    auto_detect: true

# Plugins
plugins:
  enabled: ["sora-voip", "sora-hermes"]

# Tools
tools:
  opencode:
    enabled: true
    auto_detect: true
  codex:
    enabled: true
  gemini_harness:
    enabled: false

# OpenWakeWord
openwakeword:
  enabled: false
  model_path: "~/.sora/openwakeword/hey_sora.onnx"
```