# S0RA Agent

> **Voice-First AI Assistant** — Standalone CLI for Gemini Live, Vapi, and MCP voice bridges. Mirrors Hermes CLI architecture.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

S0RA Agent is a standalone command-line application built around **Gemini Live**, **Vapi.ai**, and **MCP** (Model Context Protocol) functionality. It mirrors the Hermes Agent CLI architecture while being purpose-built for real-time voice interactions.

## Features

### 🎤 Voice Bridges
- **Gemini Live** — Direct streaming to Google's Multimodal Live API with native audio
- **Vapi.ai** — Managed conversational AI platform with WebSocket transport
- **ElevenLabs** — High-quality conversational AI voices (planned)
- **Edge TTS** — Free Microsoft neural voices for testing

### 🔌 MCP Integration
- Built-in MCP server with stdio, SSE, and streamable-http transports
- Auto-detection of running MCP servers on device
- Catalog of 11 common MCP servers (filesystem, GitHub, databases, browser, Slack, Notion, Google Drive, memory, Brave Search, fetch)

### 🧙 Interactive Setup Wizard
- 7-section guided configuration (Model, Discord, Voice, MCP, Memory, Tools, Wake Word)
- **OpenClaw migration** — Detects and imports settings from ~/.openclaw
- **OpenWakeWord** — Optional "Hey Sora" wake word detection (fully local)
- Animated spinners and ASCII art throughout
- ASCII art logo and colored terminal output

### 🎨 Terminal UI (TUI)
- Ink/React-based TUI with keyboard navigation
- Voice bridge control panel
- Provider management
- System status dashboard
- Benchmark runner
- Doctor diagnostics
- Setup wizard

### 📊 Web Dashboard
- Live voice demo preview
- Provider toggle panel
- System status monitor
- Install guide with copy-paste commands
- Full documentation

### 🏥 Doctor & Benchmarks
- Comprehensive system health checks
- Performance benchmarks (CLI startup, config load, plugin discovery, MCP start, voice status, doctor check)
- JSON output for CI/CD integration

### 🔄 Git-based Updates
- `sora update` — Pull latest changes and reinstall dependencies
- `sora update --check-only` — Check for updates without applying
- Mirrors Hermes update mechanism

## Installation

```bash
# Using pipx (recommended)
pipx install git+https://github.com/capslockb/sora-agent

# Or with uv
uv pip install git+https://github.com/capslockb/sora-agent

# Or with pip
pip install git+https://github.com/capslockb/sora-agent
```

Then run the interactive setup wizard:
```bash
sora setup
```

## Quick Start

```bash
# 1. Run setup wizard (interactive)
sora setup

# 2. Start a voice bridge (Gemini Live)
sora voice live --guild YOUR_GUILD_ID --channel YOUR_CHANNEL_ID

# 3. Or use Vapi.ai
sora voice vapi --guild YOUR_GUILD_ID --channel YOUR_CHANNEL_ID

# 4. Launch the TUI
sora tui

# 5. Check system status
sora status

# 6. Run doctor diagnostics
sora doctor

# 7. Run performance benchmarks
sora benchmark
```

## Commands

| Command | Description |
|---------|-------------|
| `sora` / `sora chat` | Start interactive chat session |
| `sora setup` | Run interactive setup wizard |
| `sora voice live` | Start Gemini Live voice bridge |
| `sora voice vapi` | Start Vapi.ai voice bridge |
| `sora voice status` | Show voice bridge status |
| `sora voice leave` | Stop voice bridge |
| `sora voice providers` | Manage voice providers (TTS/STT/LLM Voice) |
| `sora mcp start` | Start MCP server |
| `sora mcp status` | Show MCP server status |
| `sora mcp list` | List available MCP servers |
| `sora mcp catalog` | Browse MCP server catalog |
| `sora status` | Show system health dashboard |
| `sora doctor` | Run diagnostics |
| `sora benchmark` | Run performance benchmarks |
| `sora config` | Configuration management |
| `sora plugins` | Plugin management |
| `sora skills` | Skill management |
| `sora cron` | Cron job management |
| `sora logs` | View logs |
| `sora tui` | Launch Terminal UI (Ink/React) |
| `sora update` | Update to latest version |
| `sora version` | Show version |
| `sora acp` | Run as ACP server for editor integration |

## Voice Providers

```bash
# List available providers
sora voice providers list

# Enable a provider
sora voice providers enable gemini-live
sora voice providers enable vapi
sora voice providers enable elevenlabs
sora voice providers enable edge-tts

# Disable a provider
sora voice providers disable vapi
```

## Configuration

Configuration is stored in `~/.sora/config.yaml` and secrets in `~/.sora/.env`.

### Profiles
Supports multiple isolated profiles like Hermes:
```bash
sora --profile myprofile setup
sora --profile myprofile chat
```

Profiles are stored in `~/.sora-profiles/` or `~/.sora-<name>/`.

## Hermes Plugin

S0RA also works as a Hermes plugin. Install:

```bash
# Copy plugin to Hermes
cp -r plugins/sora_hermes ~/.hermes/plugins/

# Enable in Hermes
hermes plugins enable sora-hermes
```

This registers these tools in Hermes:
- `sora_voice_live` — Start Gemini Live bridge
- `sora_voice_vapi` — Start Vapi bridge
- `sora_voice_leave` — Stop voice bridge
- `sora_voice_status` — Check bridge status
- `sora_mcp_start` — Start MCP server
- `sora_mcp_status` — Get MCP server status

And Discord slash commands:
- `/sora-voice-live`
- `/sora-voice-vapi`

## Architecture

S0RA mirrors Hermes CLI architecture:

```
sora-agent/
├── sora_bootstrap.py       # UTF-8 stdio setup (Windows)
├── sora_constants.py       # Profile-aware paths
├── sora_logging.py         # Centralized logging
├── sora_cli/               # CLI commands
│   ├── main.py             # Entry point & parser
│   ├── setup.py            # Interactive setup wizard
│   ├── voice.py            # Voice bridge management
│   ├── mcp.py              # MCP server management
│   ├── status.py           # System status dashboard
│   ├── doctor.py           # Diagnostics
│   ├── benchmark.py        # Performance benchmarks
│   ├── config.py           # Config management
│   ├── plugins.py          # Plugin management
│   ├── skills.py           # Skill management
│   ├── cron.py             # Cron jobs
│   ├── tui.py              # TUI launcher
│   └── skin_engine.py      # Theme/skin system
├── plugins/
│   └── sora_hermes/        # Hermes plugin
├── ui-tui/                 # Ink/React TUI
├── website/                # React web dashboard
├── agent/                  # Agent core (optional)
└── tests/                  # Test suite
```

## Requirements

- Python 3.11+
- Node.js 20+ (for TUI and website)
- Git
- Discord Bot Token (for voice bridges)
- Gemini API Key (for Gemini Live)
- Vapi API Key (optional, for Vapi bridge)

## Optional Dependencies

```bash
# Voice bridges
pip install "sora-agent[gemini-live,vapi]"

# Web search backends
pip install "sora-agent[exa,firecrawl,parallel-web]"

# Image generation
pip install "sora-agent[fal]"

# TTS/STT
pip install "sora-agent[edge-tts,elevenlabs,minimax-tts,openai-tts,faster-whisper]"

# MCP
pip install "sora-agent[mcp]"

# Web dashboard
pip install "sora-agent[web]"

# All optional
pip install "sora-agent[all]"
```

## Development

```bash
# Clone repo
git clone https://github.com/capslockb/sora-agent
cd sora-agent

# Install in development mode
uv pip install -e ".[dev]"

# Run tests
pytest

# Build TUI
cd ui-tui && npx esbuild src/cli.tsx --bundle --platform=node --outfile=dist/cli.js --external:ink --external:react --format=esm

# Build website
cd website && npm run build

# Run linting
ruff check .
```

## License

MIT License — see [LICENSE](LICENSE) for details.

## Related Projects

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — The agent that grows with you
- [OpenClaw](https://github.com/openclaw/openclaw) — Personal AI assistant (migratable)
- [Discord Voice Plugin](https://github.com/capslockb/hermes-plugins/tree/main/discord-voice) — Original Gemini Live bridge