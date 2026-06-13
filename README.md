# S0RA Agent

**S0RA Agent** is a standalone CLI application for voice-first AI interaction, built around:
- **Gemini Live** — Google's multimodal live streaming API
- **Vapi.ai** — Managed conversational AI platform
- **MCP** — Model Context Protocol for external tool integration

S0RA mirrors the **Hermes Agent** CLI architecture (`sora`, `sora setup`, `sora chat`, etc.) while being purpose-built for voice bridges. It also works as a **Hermes plugin** so you can use Sora's voice bridges from within Hermes.

## Features

- 🎙️ **Gemini Live Voice Bridge** — Real-time voice streaming with Google's Gemini models
- 🤖 **Vapi.ai Voice Bridge** — Managed conversational AI with dashboard, phone, and web support
- 🔌 **MCP Integration** — Connect to filesystem, GitHub, databases, browser automation, and more
- 🧠 **Honcho Memory** — Persistent cross-session memory
- 🎨 **Hermes-compatible CLI** — `sora`, `sora setup`, `sora chat`, `sora voice`, `sora mcp`, `sora status`, etc.
- 🔌 **Hermes Plugin** — Use Sora's tools from within Hermes Agent

## Installation

### Standalone (recommended)

```bash
# From source
git clone https://github.com/capslockb/sora-agent
cd sora-agent
pipx install -e .

# Or with uv
uv pip install -e .
```

### As Hermes Plugin

```bash
# From within Hermes
hermes plugins install capslockb/sora-agent

# Or manually
mkdir -p ~/.hermes/plugins/sora-hermes
# Copy plugin files
hermes plugins enable sora-hermes
```

## Quick Start

```bash
# 1. Run setup wizard
sora setup

# 2. Start a voice bridge
sora voice live --guild YOUR_GUILD_ID --channel YOUR_CHANNEL_ID

# Or Vapi
sora voice vapi --guild YOUR_GUILD_ID --channel YOUR_CHANNEL_ID

# 3. Start MCP server
sora mcp start

# 4. Check status
sora status
```

## Architecture

```
sora-agent/
├── sora_cli/           # Main CLI package
│   ├── main.py         # Entry point (sora command)
│   ├── setup.py        # Interactive setup wizard
│   ├── voice.py        # Voice bridge commands
│   ├── mcp.py          # MCP server commands
│   ├── config.py       # Configuration management
│   ├── cli.py          # Interactive chat REPL
│   └── ...             # Other subcommands
├── plugins/
│   └── sora-hermes/    # Hermes plugin
├── pyproject.toml      # Package config
└── README.md
```

## Configuration

S0RA stores config in `~/.sora/`:
- `config.yaml` — Settings (model, voice, MCP, etc.)
- `.env` — API keys and secrets
- `plugins/` — User-installed plugins
- `skills/` — User skills
- `logs/` — Log files
- `sessions/` — Chat sessions

## Voice Bridges

### Gemini Live
Direct streaming to Google's Generative Language API.
- Low latency (~200-400ms)
- Supports video frames (1fps)
- Custom system prompt (S0RA personality)
- Honcho memory integration

### Vapi.ai
Managed conversational AI platform.
- Dashboard for assistant management
- Phone number integration
- Web embed support
- Multi-provider voice/TTS

## MCP Servers

Configure MCP servers in `sora setup` or `~/.sora/config.yaml`:

```yaml
mcp:
  enabled: true
  servers:
    filesystem:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
    github:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-github"]
      env:
        GITHUB_TOKEN: "${GITHUB_TOKEN}"
```

## Hermes Plugin Usage

Once enabled in Hermes, these tools are available:
- `sora_voice_live` — Start Gemini Live bridge
- `sora_voice_vapi` — Start Vapi bridge
- `sora_voice_leave` — Stop voice bridge
- `sora_voice_status` — Check bridge status
- `sora_mcp_start` — Start MCP server
- `sora_mcp_status` — Check MCP status

And slash commands in Discord:
- `/sora-voice-live` — Start Gemini Live (use discord-voice plugin instead)
- `/sora-voice-vapi` — Start Vapi (use discord-vapi plugin instead)

## Requirements

- Python 3.11+
- Node.js + npm (for MCP servers)
- Discord bot with voice permissions
- API keys: GEMINI_API_KEY, VAPI_API_KEY, DISCORD_BOT_TOKEN

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/

# Type check
ty check
```

## License

MIT — See LICENSE file.