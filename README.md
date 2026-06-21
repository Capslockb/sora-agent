<div align="center">

# S0RA Agent

### Hermes-aligned CLI and plugins for real-time voice bridges.

**One companion layer. Multiple voice providers. No isolation fantasy.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-00E0FF?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![MIT License](https://img.shields.io/badge/License-MIT-915eff?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)]()
[![Hermes](https://img.shields.io/badge/Hermes-Aligned-915eff?style=for-the-badge)](https://hermes-agent.nousresearch.com)

[**Website**](website/) · [**Install**](#install) · [**Quick Start**](#quick-start) · [**Architecture**](#architecture) · [**Bridge Elements**](#s0ra-bridge-elements) · [**Release Readiness**](docs/release-readiness.md)

</div>

---

## What this release is

S0RA Agent is a **voice companion layer** for Hermes-style agents. It keeps the useful CLI and plugin pieces for real-time voice, MCP, and VOIP control without pretending to be a separate isolated chat assistant.

This release ships a working CLI (`sora`), a FastAPI dashboard, a Hermes plugin (`sora-hermes`), a VOIP plugin (`sora-voip`), and scaffolding for seven voice providers. The live Discord voice bridge is **not spawned by this repo alone** — it is provided by the separate Hermes `discord-voice` plugin, which S0RA can configure, query, and extend.

> **Relationship to the Gemini bridge:** S0RA shares the same bridge-element philosophy as [`gemini-live-discord-bridge`](https://github.com/Capslockb/gemini-live-discord-bridge) — operator-facing tools, a sidecar health surface, status truth-tagging, and a public docs/site. It is a **separate product/runtime**: Gemini bridge is a single Discord voice bridge; S0RA is a multi-provider companion CLI and plugin registry.

---

## Status map

| Area | Status | Truthful scope |
|---|---|---|
| CLI entry (`sora --help`, `sora status`, `sora doctor`) | **WORKING** | Verified commands. 17 pytest tests pass. |
| Setup wizard (`sora setup`) | **WORKING** | Interactive provider/API-key configuration. |
| Provider registry (`sora voice providers`) | **WORKING** | List/enable/disable TTS/STT/LLM-voice providers. |
| ElevenLabs signed URLs / WebSocket targets | **WORKING** | URL generation and bridge prep implemented. |
| FastAPI dashboard (`/health`, `/api/status`) | **WORKING** | Default port `8080`. Verified with `TestClient`. |
| Hermes plugin (`sora-hermes`) | **WORKING** | Registers `sora_voice_*` and `sora_mcp_*` tools. |
| Discord voice bridges (`sora voice live/vapi/…`) | **PARTIAL** | CLI validates config and prepares bridge args. Live bridging requires the Hermes `discord-voice` plugin runtime. |
| MCP server management | **PARTIAL** | Start/status/catalog CLI works; WebSocket/SSE paths are scaffolding. |
| VOIP Asterisk + Dograh bridge (`sora-voip`) | **PARTIAL** | Plugin and ARI/SIP commands exist. Needs Asterisk/Dograh runtime. |
| TUI mode (`sora tui`) | **PLANNED** | Stub falls back to REPL. Not a real Ink/React TUI yet. |
| Interactive cron creation (`sora cron`) | **PLANNED** | List/show works; create/run are stubs. |
| Skill search/browse/audit (`sora skills`) | **PLANNED** | Commands exist but operations are not implemented. |
| Session log filtering (`sora logs`) | **PLANNED** | View works; filtering is not implemented. |
| Doctor auto-fix (`sora doctor --fix`) | **PLANNED** | Diagnostics work; auto-fix is a stub. |
| ACP adapter (`sora acp`) | **RESEARCH** | Entry point stub; no full ACP server implementation. |

See [`docs/release-readiness.md`](docs/release-readiness.md) for the full truth table, hard release rules, and E2E smoke checklist.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  User surface: sora CLI  │  FastAPI dashboard  │  Hermes chat (via plugin)   │
└──────────────────────────┴─────────────────────┴───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       S0RA CLI / API layer                                  │
│  setup · voice · mcp · status · doctor · config · plugins · skills · cron │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────────────┐
│ sora-hermes   │      │ sora-voip     │      │ built-in runtime      │
│ plugin        │      │ plugin        │      │ (MCP scaffolds,       │
│               │      │               │      │  provider registry,   │
│ Registers     │      │ Asterisk ARI  │      │  FastAPI dashboard)   │
│ sora_voice_*  │      │ + Dograh      │      │                       │
│ tools in      │      │ SIP/RTP       │      │                       │
│ Hermes        │      │               │      │                       │
└───────┬───────┘      └───────┬───────┘      └───────────┬───────────┘
        │                      │                          │
        ▼                      ▼                          ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────────────┐
│ Hermes        │      │ Asterisk      │      │ Provider backends     │
│ discord-voice │      │ PBX + Dograh  │      │ (Gemini, Vapi,       │
│ plugin        │      │ gateway       │      │ ElevenLabs, OpenAI,   │
│               │      │               │      │ xAI, Ultravox, Retell)│
│ Live bridge   │      │ Phone bridge  │      │                       │
│ runtime       │      │ runtime       │      │                       │
└───────────────┘      └───────────────┘      └───────────────────────┘
```

Read the full design in [`docs/guide/architecture.md`](docs/guide/architecture.md).

---

## Quick start

```bash
# 1. Install
pipx install git+https://github.com/Capslockb/sora-agent
# or: git clone ... && pip install -e .

# 2. Run the setup wizard
sora setup

# 3. Verify the install
sora --version
sora doctor
sora status

# 4. Check provider state
sora voice providers list

# 5. Start the dashboard (optional)
sora dashboard start --port 8080
# Open http://127.0.0.1:8080/health
```

### Verification commands

```bash
sora --help
sora status --json
sora voice status
sora mcp status
python -m pytest tests/ -q
```

See [`docs/guide/quick-start.md`](docs/guide/quick-start.md) for install pitfalls and next steps.

---

## S0RA bridge elements

S0RA exposes a small operator-friendly tool surface. When the `sora-hermes` plugin is enabled, these tools register in Hermes:

| Tool | Status | What it does |
|---|---|---|
| `sora_voice_live` | **PARTIAL** | Prepare/start Gemini Live Discord bridge args. Runtime provided by Hermes `discord-voice`. |
| `sora_voice_vapi` | **PARTIAL** | Prepare/start Vapi Discord bridge args. Runtime provided by Hermes `discord-voice`. |
| `sora_voice_leave` | **PARTIAL** | Stop active voice bridge via Hermes `discord-voice`. |
| `sora_voice_status` | **WORKING** | Return structured voice bridge status from S0RA state. |
| `sora_mcp_start` | **PARTIAL** | Start MCP server (stdio supported; HTTP/SSE scaffolding). |
| `sora_mcp_status` | **WORKING** | Return MCP server status. |

Read the deep doc in [`docs/bridge-elements.md`](docs/bridge-elements.md).

---

## Feature matrix

| Feature | Status | Doc | Caveat |
|---|---|---|---|
| CLI help/version/status/doctor | **WORKING** | [`reference/cli/sora.md`](docs/reference/cli/sora.md) | — |
| Setup wizard | **WORKING** | [`reference/cli/setup.md`](docs/reference/cli/setup.md) | — |
| Provider enable/disable | **WORKING** | [`guide/voice/providers.md`](docs/guide/voice/providers.md) | — |
| ElevenLabs URL signing | **WORKING** | [`guide/voice/elevenlabs.md`](docs/guide/voice/elevenlabs.md) | — |
| FastAPI dashboard | **WORKING** | [`reference/cli/dashboard.md`](docs/reference/cli.md) | Default port `8080`. |
| Hermes plugin tools | **WORKING** | [`reference/plugins/sora-hermes.md`](docs/reference/plugins/sora-hermes.md) | Requires `discord-voice` for live audio. |
| Discord voice bridges | **PARTIAL** | [`guide/voice/gemini-live.md`](docs/guide/voice/gemini-live.md) | Live runtime in Hermes `discord-voice`. |
| VOIP Asterisk/Dograh | **PARTIAL** | [`voip/setup.md`](docs/voip/setup.md) | Needs PBX runtime. |
| MCP server | **PARTIAL** | [`guide/mcp/servers.md`](docs/guide/mcp/servers.md) | stdio works; WS/HTTP scaffolding. |
| TUI | **PLANNED** | [`reference/cli/tui.md`](docs/reference/cli/tui.md) | Stub only. |
| Cron | **PLANNED** | [`reference/cli/cron.md`](docs/reference/cli.md) | Partial. |
| Skills | **PLANNED** | [`reference/cli/skills.md`](docs/reference/cli.md) | Partial. |
| Logs | **PLANNED** | [`reference/cli/logs.md`](docs/reference/cli.md) | Partial. |
| Doctor auto-fix | **PLANNED** | [`reference/cli/doctor.md`](docs/reference/cli/doctor.md) | Partial. |
| ACP adapter | **RESEARCH** | [`reference/cli/acp.md`](docs/reference/cli.md) | Stub only. |

---

## Required environment

The three critical pieces of configuration:

```bash
# ~/.sora/.env
GEMINI_API_KEY=...            # For Gemini Live bridge
DISCORD_BOT_TOKEN=...         # For Discord voice bridges (Hermes discord-voice)
ELEVENLABS_API_KEY=...        # Optional, for ElevenLabs bridge
```

See [`docs/env-vars.md`](docs/env-vars.md) for the exhaustive grouped reference.

---

## Sidecar HTTP control API

The S0RA dashboard exposes local control endpoints on the configured port (default `8080`):

| Method | Path | Description | Status |
|---|---|---|---|
| GET | `/health` | API liveness | **WORKING** |
| GET | `/api/status` | Voice/MCP/VOIP/system status | **WORKING** |
| GET | `/api/visualizer/state` | UI-friendly visualizer snapshot | **WORKING** |
| GET | `/api/dashboard/stats` | CPU/memory metrics | **WORKING** |
| POST | `/api/voice/start` | Prepare voice bridge start | **PARTIAL** |
| POST | `/api/mcp/start` | Start MCP server | **PARTIAL** |

Full route list in [`docs/bridge-elements.md`](docs/bridge-elements.md).

---

## What this repo does not currently ship

To prevent over-promising:

- **A standalone live Discord voice bridge.** The audio path lives in the Hermes `discord-voice` plugin. S0RA configures and queries it.
- **A hosted phone service.** VOIP requires your own Asterisk PBX and Dograh gateway.
- **A cloud transcription API.** S0RA can point at external Whisper endpoints, but does not host one.
- **A finished TUI.** `sora tui` is a stub.
- **A finished ACP server.** `sora acp` is a research stub.
- **Auto-fix diagnostics.** `sora doctor --fix` is not implemented.

---

## Release verification checklist

```bash
# 1. CLI sanity
sora --help
sora --version

# 2. Health checks
sora doctor
sora status
sora voice status
sora mcp status

# 3. API health
curl -s http://127.0.0.1:8080/health | python3 -m json.tool

# 4. Test suite
python -m pytest tests/ -q

# 5. Hermes plugin registration (when Hermes is installed)
hermes plugins enable sora-hermes
hermes tools list | grep sora_
```

Expected results: CLI returns `0`, doctor reports no hard failures, API returns `{"status":"healthy"}`, tests pass.

---

## Documentation

- [`docs/guide/quick-start.md`](docs/guide/quick-start.md) — install, first commands, pitfalls
- [`docs/guide/architecture.md`](docs/guide/architecture.md) — system map, audio path, integration boundaries
- [`docs/bridge-elements.md`](docs/bridge-elements.md) — operator tools, sidecar API, wiring
- [`docs/env-vars.md`](docs/env-vars.md) — exhaustive env var reference
- [`docs/release-readiness.md`](docs/release-readiness.md) — status legend, truth table, release blockers
- [`docs/troubleshooting.md`](docs/troubleshooting.md) — common failures and log locations
- [`docs/.vitepress/config.mts`](docs/.vitepress/config.mts) — VitePress docs-site nav

---

## License

MIT — see [`LICENSE`](LICENSE).
