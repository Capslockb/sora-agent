# S0RA Agent / SORA Bridge

> **SORA Bridge control layer** — CLI, FastAPI backend, Hermes plugin, MCP tooling, VOIP controls, TUI work, and the migration target for the older Gemini Discord bridge.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

## Status: active transition from Gemini Bridge

S0RA Agent is the new home for the broader **SORA Bridge** layer. It is not yet a complete drop-in replacement for [`Capslockb/gemini-live-discord-bridge`](https://github.com/Capslockb/gemini-live-discord-bridge).

Current split:

| Area | Current source of truth |
|---|---|
| Working live Discord/Gemini audio runtime | `Capslockb/gemini-live-discord-bridge` |
| SORA CLI, config, status, doctor, profiles | this repo |
| Hermes SORA plugin tools | this repo, `plugins/sora_hermes/` |
| FastAPI dashboard/control backend | this repo, `sora-api` / `sora_api.py` |
| MCP management | this repo |
| VOIP/SIP/ARI/Dograh control surface | this repo |
| Full SORA-owned provider runtime | in progress |

The README has been rewritten to match the current code more honestly. Earlier docs overstated the live bridge/runtime side. The code currently contains strong scaffolding and control surfaces, while the actual long-running Gemini Discord bridge still lives in the Gemini bridge repo until it is transplanted or wrapped cleanly.

---

## What works today

| Capability | Current state |
|---|---|
| `sora` CLI | Main command entrypoint |
| `sora setup` | Interactive setup wizard / configuration path |
| `sora status` | Component status dashboard |
| `sora doctor` | Diagnostics path |
| `sora benchmark` | Benchmark command path |
| Profiles | `--profile` / `SORA_HOME` profile-aware paths |
| TUI | Ink/React TUI package exists under `ui-tui/` |
| MCP | Start/status/list/catalog/ws command surface |
| Hermes plugin | Registers `sora_voice_*` and `sora_mcp_*` tools |
| FastAPI API | `sora-api` script exposes `/health`, `/api/status`, voice/config/MCP endpoints |
| VOIP controls | SIP, ARI, call, hangup, voip-status, voip-config command surface |

## What is still in progress

| Area | Reality |
|---|---|
| `sora voice live` | Validates config and returns a Gemini Live bridge-start status; the full Discord/Gemini runtime is not yet transplanted from the old bridge |
| `sora voice vapi` | Validates config and returns a Vapi bridge-start status; long-running Vapi runtime integration still needs hardening |
| `sora voice status` | Currently returns empty/no active bridges unless backed by future runtime state |
| Dashboard frontend | Backend API exists; frontend/web docs may lag behind code |
| Hermes slash commands | Registered as compatibility hints; the active live Discord command remains `/voice-live` from the old Gemini bridge until migration is complete |

---

## Installation

```bash
# Using pipx
pipx install git+https://github.com/capslockb/sora-agent

# Or with uv
uv pip install git+https://github.com/capslockb/sora-agent

# Or with pip
pip install git+https://github.com/capslockb/sora-agent
```

For development:

```bash
git clone https://github.com/capslockb/sora-agent
cd sora-agent
uv pip install -e ".[dev]"
```

---

## Quick start

```bash
# Configure SORA
sora setup

# Check local state
sora status
sora doctor

# Launch the terminal UI
sora tui

# Start the API backend
sora-api
```

Voice bridge commands exist, but treat Gemini/Vapi startup as **migration scaffolding** until the runtime move is complete:

```bash
# Gemini Live bridge control path — scaffold/status path for now
sora voice live --guild YOUR_GUILD_ID --channel YOUR_CHANNEL_ID

# Vapi bridge control path — scaffold/status path for now
sora voice vapi --guild YOUR_GUILD_ID --channel YOUR_CHANNEL_ID

# Stop/status paths
sora voice status
sora voice leave --guild YOUR_GUILD_ID
```

For the current working Discord/Gemini voice runtime, use the older bridge repo for now:

```bash
git clone https://github.com/Capslockb/gemini-live-discord-bridge.git
cd gemini-live-discord-bridge
./install.sh
systemctl --user restart hermes-gateway
# then in Discord:
/voice-live
```

---

## Main commands

| Command | Description |
|---|---|
| `sora` / `sora chat` | Interactive chat session |
| `sora setup` | Setup wizard / configuration |
| `sora status` | System status dashboard |
| `sora doctor` | Diagnostics |
| `sora benchmark` | Performance benchmarks |
| `sora config` | Configuration management |
| `sora plugins` | Plugin management |
| `sora skills` | Skill management |
| `sora cron` | Cron job management |
| `sora logs` | View logs |
| `sora tui` | Launch terminal UI |
| `sora update` | Update from git |
| `sora uninstall` | Uninstall SORA Agent |
| `sora version` | Version info |
| `sora acp` / `sora-acp` | ACP/editor integration |
| `sora-api` | FastAPI backend server |
| `sora-voip` | VOIP plugin CLI entrypoint |

### Voice commands

| Command | Description |
|---|---|
| `sora voice live` | Gemini Live bridge control path; runtime migration still pending |
| `sora voice vapi` | Vapi bridge control path; runtime hardening still pending |
| `sora voice elevenlabs` | ElevenLabs bridge control path |
| `sora voice status` | Show current voice bridge status |
| `sora voice leave` | Stop voice bridge(s) |
| `sora voice providers list` | List configured providers |
| `sora voice providers enable <provider>` | Enable a provider |
| `sora voice providers disable <provider>` | Disable a provider |
| `sora voice providers config <provider>` | Configure a provider |
| `sora voice sip register/status/unregister` | SIP registration control |
| `sora voice ari connect/status/apps/disconnect` | Asterisk ARI control |
| `sora voice call <number>` | Place an outbound call through VOIP bridge |
| `sora voice hangup --channel <id>` / `--all` | Hang up call(s) |
| `sora voice voip-status` | Show VOIP bridge status |
| `sora voice voip-config show/set/reload` | Manage VOIP config |

### MCP commands

| Command | Description |
|---|---|
| `sora mcp start` | Start MCP server |
| `sora mcp status` | Show MCP status |
| `sora mcp stop` | Stop MCP server |
| `sora mcp list` | List available MCP servers |
| `sora mcp catalog` | Browse MCP server catalog |
| `sora mcp ws ...` | WebSocket MCP management |

---

## Configuration

Configuration is stored under SORA home paths:

```text
~/.sora/config.yaml
~/.sora/.env
```

Profiles are supported:

```bash
sora --profile myprofile setup
sora --profile myprofile chat
```

Common environment variables:

```bash
GEMINI_API_KEY=***
GOOGLE_API_KEY=***
VAPI_API_KEY=***
ELEVENLABS_API_KEY=***
DISCORD_BOT_TOKEN=***
DISCORD_APPLICATION_ID=***
HONCHO_API_KEY=***
SORA_ARI_URL=***
SORA_ARI_USER=***
SORA_ARI_PASSWORD=***
SORA_DOGRAH_WS_URL=***
SORA_DOGRAH_API_KEY=***
```

---

## Hermes plugin

SORA also ships a Hermes plugin:

```bash
cp -r plugins/sora_hermes ~/.hermes/plugins/
hermes plugins enable sora-hermes
```

The plugin registers these Hermes tools:

- `sora_voice_live`
- `sora_voice_vapi`
- `sora_voice_leave`
- `sora_voice_status`
- `sora_mcp_start`
- `sora_mcp_status`

Important: the registered Discord slash commands are currently compatibility guidance. For live Gemini Discord audio, continue using `/voice-live` from `gemini-live-discord-bridge` until the runtime migration is finished.

---

## API backend

Run:

```bash
sora-api
```

Default bind is read from SORA config, falling back to:

```text
0.0.0.0:8080
```

Implemented API groups include:

- `/health`
- `/api/status`
- `/api/dashboard/stats`
- `/api/dashboard/calls`
- `/api/voice/status`
- `/api/voice/start`
- `/api/voice/stop`
- `/api/providers/select`
- `/api/config`
- `/api/config/env`
- `/api/mcp/status`
- `/api/mcp/servers`
- `/api/mcp/detect`
- `/api/mcp/start`
- `/api/mcp/stop`
- `/api/mcp/ws/status`
- `/api/mcp/ws/start`
- `/api/mcp/ws/stop`

Some endpoints currently save config and return intended state rather than starting a long-running provider runtime. Treat this API as the control/backend layer under active buildout.

---

## Architecture

```text
sora-agent/
├── sora_bootstrap.py          # UTF-8 stdio setup
├── sora_constants.py          # SORA_HOME/profile-aware paths
├── sora_logging.py            # Logging setup
├── sora_api.py                # FastAPI backend
├── sora_cli/                  # CLI commands
│   ├── main.py                # Main parser / dispatch
│   ├── setup.py               # Setup wizard
│   ├── voice.py               # Voice/VOIP command handlers
│   ├── mcp.py                 # MCP management
│   ├── status.py              # Status dashboard
│   ├── doctor.py              # Diagnostics
│   ├── benchmark.py           # Benchmarks
│   ├── config.py              # Config/env helpers
│   ├── plugins.py             # Plugin management
│   ├── skills.py              # Skill management
│   ├── cron.py                # Cron jobs
│   └── tui.py                 # TUI launcher
├── plugins/
│   └── sora_hermes/           # Hermes plugin
├── plugins/sora_voip/         # VOIP plugin package
├── ui-tui/                    # Ink/React terminal UI
├── agent/                     # Agent core
├── gateway/                   # Gateway components
├── providers/                 # Provider integrations
└── tests/                     # Test suite
```

---

## Optional dependencies

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

# API/backend web dependencies
pip install "sora-agent[web]"

# All optional extras
pip install "sora-agent[all]"
```

---

## Development

```bash
# Install editable dev build
uv pip install -e ".[dev]"

# Run tests
pytest

# Build TUI
cd ui-tui
npm install
npm run build

# Run linting
ruff check .
```

---

## Migration target

SORA Bridge should eventually absorb or wrap the working pieces of the Gemini bridge:

1. provider registry and config in SORA;
2. API/TUI control in SORA;
3. Hermes tool surface in SORA;
4. Gemini Live Discord runtime transplanted from `gemini-live-discord-bridge`;
5. old README/docs-site regenerated or retired after code and docs match.

Until then, keep both repos documented separately: Gemini bridge for the current live Discord/Gemini runtime, SORA bridge for the future shared control layer.

---

## Related projects

- [`Capslockb/gemini-live-discord-bridge`](https://github.com/Capslockb/gemini-live-discord-bridge) — current live Gemini Discord voice bridge.
- [`Capslockb/hermes-agent`](https://github.com/Capslockb/hermes-agent) — Hermes host environment.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
