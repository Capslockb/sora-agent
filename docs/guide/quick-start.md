# Quick Start

## 1. Install

```bash
# Recommended: pipx (isolated, auto-updatable)
pipx install git+https://github.com/Capslockb/sora-agent

# Or development install
git clone https://github.com/Capslockb/sora-agent
cd sora-agent
pip install -e .
```

## 2. Run Setup Wizard

```bash
sora setup
```

The interactive wizard guides you through:

1. **Model Provider** — OpenRouter, Ollama, etc.
2. **Discord Bot** — Token, Guild ID, Channel ID
3. **Voice Bridges** — Gemini Live, Vapi, ElevenLabs, OpenAI Realtime, xAI Grok, Ultravox, Retell AI (Discord)
4. **VOIP Integration** — Asterisk ARI, Dograh/Gemini Live (phone)
5. **MCP** — Auto-detect running servers, configure stdio/HTTP
6. **Memory** — Honcho, OpenClaw, or Hermes memory passthrough
7. **Providers** — Enable/disable TTS/STT/LLM Voice
8. **Tools** — OpenCode, Codex, Gemini Harness
9. **OpenWakeWord** — "Hey Sora" hotword detection

Or quick-setup a specific voice provider (prompts only the relevant API keys):

```bash
sora setup --provider gemini-live        # Gemini API key
sora setup --provider vapi               # Vapi API key
sora setup --provider elevenlabs         # ElevenLabs API key + Agent ID
sora setup --provider openai-realtime    # OpenAI API key
sora setup --provider xai-grok           # xAI API key
sora setup --provider ultravox           # Ultravox API key
sora setup --provider retell             # Retell API key + Agent ID
```

## 3. Start Voice Bridge (Discord)

```bash
# Gemini Live (requires GEMINI_API_KEY + DISCORD_BOT_TOKEN)
sora voice live --guild <GUILD_ID> --channel <CHANNEL_ID>

# Vapi.ai (requires VAPI_API_KEY)
sora voice vapi --guild <GUILD_ID> --channel <CHANNEL_ID>

# ElevenLabs (requires ELEVENLABS_API_KEY)
sora voice elevenlabs --guild <GUILD_ID> --channel <CHANNEL_ID>

# OpenAI Realtime (requires OPENAI_API_KEY)
sora voice openai --guild <GUILD_ID> --channel <CHANNEL_ID>

# xAI Grok (requires XAI_API_KEY)
sora voice xai --guild <GUILD_ID> --channel <CHANNEL_ID>

# Ultravox (requires ULTRAVOX_API_KEY)
sora voice ultravox --guild <GUILD_ID> --channel <CHANNEL_ID>

# Retell AI (requires RETELL_API_KEY)
sora voice retell --guild <GUILD_ID> --channel <CHANNEL_ID>
```

## 4. Check Status

```bash
sora status          # Overall system status
sora voice status    # Voice bridges
sora mcp status      # MCP servers
sora doctor          # Health check
```

## 5. Launch Web Dashboard

```bash
sora dashboard start --port 3000
# Open http://localhost:3000
```

## 6. Launch TUI

```bash
sora tui --build     # First run (builds Ink/React)
sora tui             # Subsequent runs
