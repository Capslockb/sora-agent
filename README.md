# S0RA Agent / SORA Bridge

> A user-friendly control layer for SORA: CLI, profiles, config, FastAPI backend, MCP tools, Hermes integration, VOIP controls, and the migration home for the future SORA voice bridge.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Migration-yellow.svg)]()

## Read this first

SORA Bridge is **not yet the production Discord/Gemini voice runtime**.

Today, this repo is best used for:

- setting up and managing SORA profiles;
- running the `sora` CLI;
- starting the FastAPI control/backend server;
- managing MCP configuration and status;
- experimenting with VOIP/SIP/ARI/Dograh control surfaces;
- installing the Hermes-facing SORA plugin;
- preparing the migration path away from the older Gemini bridge.

For the currently working live Discord + Gemini audio bridge, continue using:

```text
Capslockb/gemini-live-discord-bridge
```

That older repo currently owns the working `/voice-live` Discord runtime. This repo is where the SORA-owned bridge layer is being built and documented.

---

## What should I use?

| Goal | Use this |
|---|---|
| Talk to Gemini Live in a Discord voice channel today | `gemini-live-discord-bridge` and `/voice-live` |
| Configure SORA, profiles, env, status, diagnostics | this repo: `sora setup`, `sora status`, `sora doctor` |
| Run the SORA API backend | this repo: `sora-api` |
| Manage MCP from SORA | this repo: `sora mcp ...` |
| Test SORA voice-provider commands | this repo: `sora voice ...`, but live/vapi/elevenlabs startup is scaffold/status until runtime transplant is complete |
| Install a Hermes SORA plugin | this repo: `plugins/sora_hermes/` |
| Build the terminal UI | this repo: `ui-tui/` |

---

## Current reality check

| Area | Current state |
|---|---|
| Package | `sora-agent`, version `0.1.0` |
| Python | `>=3.11,<3.15` |
| Main CLI | `sora = sora_cli.main:main` |
| API backend | `sora-api = sora_api:main`, FastAPI/uvicorn |
| VOIP CLI | `sora-voip = plugins.sora_voip.cli:main` |
| ACP CLI | `sora-acp = acp_adapter.entry:main` |
| Config root | `~/.sora/` by default, or `SORA_HOME` |
| Profiles | `~/.sora/profiles/<name>/` or `~/.sora-<name>/` |
| Gemini Live voice command | validates config/env and returns a start-status object; full Discord runtime is not yet transplanted |
| Vapi voice command | validates config/env and returns a start-status object; long-running runtime still needs hardening |
| ElevenLabs voice command | validates config/env and returns a start-status object; long-running runtime still needs hardening |
| SORA API voice start | saves intended provider/config and returns status; it does not currently launch a durable provider process |
| Hermes SORA slash commands | compatibility guidance; for live Gemini use `/voice-live` from `discord-voice` |
| Static docs | exist under `docs/`, but should be read with the code-grounded status notes |

Detailed status notes: [`docs/guide/sora-bridge-status.md`](docs/guide/sora-bridge-status.md)

---

## Install

Recommended isolated install:

```bash
pipx install git+https://github.com/Capslockb/sora-agent
```

Alternative install:

```bash
uv pip install git+https://github.com/Capslockb/sora-agent
# or
pip install git+https://github.com/Capslockb/sora-agent
```

Development install:

```bash
git clone https://github.com/Capslockb/sora-agent
cd sora-agent
uv pip install -e ".[dev]"
```

---

## First commands

```bash
# Configure SORA
sora setup

# Check local state
sora status
sora doctor

# Run the API backend
sora-api

# Launch the terminal UI if built/available
sora tui
```

Voice commands exist, but they are **not yet the production live Discord bridge**:

```bash
# Scaffold/control path for future Gemini Live runtime
sora voice live --guild YOUR_GUILD_ID --channel YOUR_CHANNEL_ID

# Scaffold/control path for future Vapi runtime
sora voice vapi --guild YOUR_GUILD_ID --channel YOUR_CHANNEL_ID

# Status/stop paths
sora voice status
sora voice leave --guild YOUR_GUILD_ID
```

For live Discord/Gemini audio right now:

```bash
git clone https://github.com/Capslockb/gemini-live-discord-bridge.git
cd gemini-live-discord-bridge
./install.sh
systemctl --user restart hermes-gateway
# then in Discord:
/voice-live
```

---

## Main command map

| Command | What it does |
|---|---|
| `sora` / `sora chat` | Interactive chat path |
| `sora setup` | Interactive setup wizard |
| `sora status` | Component status dashboard |
| `sora doctor` | Diagnostics and dependency checks |
| `sora benchmark` | Performance benchmark path |
| `sora config` | Configuration and env helpers |
| `sora plugins` | Plugin management |
| `sora skills` | Skill management |
| `sora cron` | Cron job management |
| `sora logs` | Log viewing |
| `sora tui` | Terminal UI launcher |
| `sora update` | Git/update path |
| `sora uninstall` | Uninstall path |
| `sora version` / `sora --version` | Version info |
| `sora acp` / `sora-acp` | ACP/editor integration |
| `sora-api` | FastAPI backend |
| `sora-voip` | VOIP plugin CLI entrypoint |

### Voice and VOIP commands

| Command | Current behavior |
|---|---|
| `sora voice live` | Validates Gemini/Discord config and returns a Gemini bridge-start status; runtime migration still pending |
| `sora voice vapi` | Validates Vapi/Discord config and returns a Vapi bridge-start status; runtime hardening still pending |
| `sora voice elevenlabs` | Validates ElevenLabs/Discord config and returns a start status; runtime hardening still pending |
| `sora voice status` | Returns status object; currently no active bridge process registry |
| `sora voice leave` | Returns stop status; durable bridge-process stop still depends on future runtime integration |
| `sora voice providers list` | List configured voice providers |
| `sora voice providers enable <provider>` | Enable provider in config |
| `sora voice providers disable <provider>` | Disable provider in config |
| `sora voice providers config <provider>` | Show guidance/config path for provider |
| `sora voice sip register/status/unregister` | SIP registration control surface |
| `sora voice ari connect/status/apps/disconnect` | Asterisk ARI control surface |
| `sora voice call <number>` | Outbound-call control path through VOIP plugin/config |
| `sora voice hangup --channel <id>` / `--all` | Hangup command path |
| `sora voice voip-status` | VOIP status command path |
| `sora voice voip-config show/set/reload` | VOIP config command path |

### MCP commands

| Command | What it does |
|---|---|
| `sora mcp start` | Start/configure MCP server path |
| `sora mcp status` | Show MCP status |
| `sora mcp stop` | Stop MCP server path |
| `sora mcp list` | List available MCP servers |
| `sora mcp catalog` | Browse MCP server catalog |
| `sora mcp ws ...` | WebSocket MCP management |

---

## Configuration

SORA stores runtime configuration under SORA home:

```text
~/.sora/config.yaml
~/.sora/.env
```

Profiles are supported through `--profile` / `-p` and `SORA_HOME`:

```bash
sora --profile default status
sora --profile myprofile setup
export SORA_HOME=~/.sora-myprofile
```

Common environment variables:

```bash
OPENROUTER_API_KEY=***
GEMINI_API_KEY=***       # or GOOGLE_API_KEY
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

More detail: [`docs/guide/configuration.md`](docs/guide/configuration.md)

---

## API backend

Run:

```bash
sora-api
```

Default bind comes from `network.http` in SORA config and falls back to:

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

Important: voice/MCP start endpoints currently save intended config and return a state response. They should not be described as guaranteed durable runtime launchers yet.

---

## Hermes plugin

SORA ships a Hermes plugin at:

```text
plugins/sora_hermes/
```

Install example:

```bash
cp -r plugins/sora_hermes ~/.hermes/plugins/
hermes plugins enable sora-hermes
```

Registered Hermes tools:

- `sora_voice_live`
- `sora_voice_vapi`
- `sora_voice_leave`
- `sora_voice_status`
- `sora_mcp_start`
- `sora_mcp_status`

The plugin also registers slash command names `sora-voice-live` and `sora-voice-vapi`, but their handlers currently return guidance to use the older dedicated Discord voice plugins. For production Gemini Live voice, use `/voice-live` from `gemini-live-discord-bridge` until SORA owns the runtime.

---

## Architecture map

```text
sora-agent/
├── sora_bootstrap.py          # UTF-8 stdio setup
├── sora_constants.py          # SORA_HOME/profile-aware paths
├── sora_logging.py            # Logging setup
├── sora_api.py                # FastAPI backend
├── sora_cli/                  # CLI commands
├── plugins/sora_hermes/       # Hermes plugin
├── plugins/sora_voip/         # VOIP plugin package
├── ui-tui/                    # Ink/React terminal UI source
├── agent/                     # Agent core
├── gateway/                   # Gateway components
├── providers/                 # Provider integration area
└── tests/                     # Test suite
```

---

## Development

```bash
uv pip install -e ".[dev]"
pytest
ruff check .

# TUI
cd ui-tui
npm install
npm run build
```

---

## Migration plan

SORA Bridge should eventually absorb or wrap the working pieces of the Gemini bridge:

1. keep provider registry and config in SORA;
2. keep API/TUI control in SORA;
3. keep Hermes tool surface in SORA;
4. transplant or wrap the working Gemini Live Discord runtime from `gemini-live-discord-bridge`;
5. retire duplicate docs once code and docs match.

Until that runtime transplant is complete, keep the repos documented separately: Gemini bridge for the current live Discord/Gemini runtime, SORA bridge for the shared control layer and future runtime home.

---

## Related projects

- [`Capslockb/gemini-live-discord-bridge`](https://github.com/Capslockb/gemini-live-discord-bridge) — current live Gemini Discord voice bridge.
- [`Capslockb/hermes-agent`](https://github.com/Capslockb/hermes-agent) — Hermes host environment.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
