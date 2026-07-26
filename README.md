<div align="center">

# S0RA Agent

### Hermes-aligned CLI and plugins for real-time voice bridges.

**One companion layer. Multiple voice providers. No isolation fantasy.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-00E0FF?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![MIT License](https://img.shields.io/badge/License-MIT-915eff?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)]()
[![Hermes](https://img.shields.io/badge/Hermes-Aligned-915eff?style=for-the-badge)](https://hermes-agent.nousresearch.com)

[**Website**](website/) · [**Install**](#quick-start) · [**Quick Start**](#quick-start) · [**Architecture**](#architecture) · [**Bridge Elements**](#s0ra-bridge-elements) · [**Release Readiness**](docs/release-readiness.md)

</div>

---

## What this release is

S0RA Agent is a **voice companion layer** for Hermes-style agents. It keeps the useful CLI and plugin pieces for real-time voice, MCP, and VOIP control without pretending to be a separate isolated chat assistant.

This release ships a working CLI (`sora`), a FastAPI dashboard, a Hermes plugin (`sora-hermes`), VOIP component and management surfaces under `sora-voip`, and scaffolding for seven voice providers. The checked-in VOIP startup entrypoints are currently blocked by local construction errors before they can connect to Asterisk or Dograh; see [Issue #14](https://github.com/Capslockb/sora-agent/issues/14). The live Discord voice bridge is **not spawned by this repo alone** — it is provided by the separate Hermes `discord-voice` plugin, which S0RA can configure, query, and extend.

> **Relationship to the Gemini bridge:** S0RA shares the same bridge-element philosophy as [`gemini-live-discord-bridge`](https://github.com/Capslockb/gemini-live-discord-bridge) — operator-facing tools, a sidecar health surface, status truth-tagging, and a public docs/site. It is a **separate product/runtime**: Gemini bridge is a single Discord voice bridge; S0RA is a multi-provider companion CLI and plugin registry.

---

## Status map

| Area | Status | Truthful scope |
|---|---|---|
| CLI entry (`sora --help`, `sora status`, `sora doctor`) | **WORKING** | Commands are implemented. Last recorded local suite: 24/24 on PR #5; current `main` is not CI-verified. |
| Setup wizard (`sora setup`, `sora setup --provider`) | **PARTIAL** | The full voice section directly configures Gemini Live and Vapi only; quick paths mainly store credentials and do not select or enable providers. The ElevenLabs quick path does not collect `ELEVENLABS_API_KEY`; see Issue #15. |
| Provider management (`sora providers`, `sora voice providers`) | **PARTIAL** | The two command families use different registries, configuration paths, provider coverage, and disable semantics; setup and the dashboard/API add more state shapes. See Issue #15. |
| ElevenLabs signed URLs / WebSocket targets | **WORKING** | URL generation and bridge prep implemented. |
| FastAPI dashboard (`/health`, `/api/status`) | **PARTIAL** | The API routes run on port `8080`, but the API is unauthenticated and defaults to `0.0.0.0`. The UI preview is launched separately, and `--host` does not constrain its bind address; treat the whole dashboard as trusted-local-development only pending Issue #13. |
| Hermes plugin (`sora-hermes`) | **WORKING** | Registers `sora_voice_*` and `sora_mcp_*` tools. |
| Discord voice bridges (`sora voice live/vapi/…`) | **PARTIAL** | CLI validates config and prepares bridge args. Live bridging requires the Hermes `discord-voice` plugin runtime. |
| MCP server management | **PARTIAL** | stdio start reaches the checked-in implementation. Status and discovery are configuration/process/port heuristics; SSE and streamable HTTP are unimplemented, and the separate raw WebSocket path is incomplete and unauthenticated. See Issue #16. |
| VOIP Asterisk + Dograh bridge (`sora-voip`) | **PARTIAL — BLOCKED** | Component and ARI/SIP management surfaces exist, but both startup entrypoints fail during local bridge construction before any PBX connection; see Issue #14. |
| TUI mode (`sora tui`) | **PARTIAL — PROTOTYPE** | Launches the checked-in Ink/React application only after a local build. Current voice, status, provider, doctor, benchmark, setup, configuration, and MCP panels use simulated, hard-coded, fixed, random, or display-only data; see Issue #17. |
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
│               │      │               │      │  provider controls,   │
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

The VOIP branch in this diagram is the intended architecture. It is not currently reachable through either checked-in VOIP startup entrypoint; see [Issue #14](https://github.com/Capslockb/sora-agent/issues/14).

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

# 4. Inspect provider state (diagnostic only)
sora providers list
sora voice providers list

# 5. Start the dashboard for local development (optional)
sora dashboard start --host 127.0.0.1 --port 3000 --api-port 8080
# API health: http://127.0.0.1:8080/health
```

> Setup and provider management are both partial. The full voice wizard directly configures only Gemini Live and Vapi, quick paths mainly store credentials, and the current ElevenLabs quick path does not collect `ELEVENLABS_API_KEY`. `sora providers`, `sora voice providers`, setup, and the dashboard/API do not share one canonical state; see [Issue #15](https://github.com/Capslockb/sora-agent/issues/15).

> `--host 127.0.0.1` constrains the FastAPI control API only. The UI preview is launched separately, and the current CLI does not pass it an explicit bind host. The dashboard also has unauthenticated sensitive routes. Run it only on a trusted local machine, and do not publish either listener through a LAN, tunnel, container port, reverse proxy, or the public internet; see [Issue #13](https://github.com/Capslockb/sora-agent/issues/13).

> `sora tui` is a separately built Ink/React prototype, not a REPL fallback or live control surface. Its current operational panels use simulated, hard-coded, fixed, random, or display-only data. Do not enter real credentials or use TUI output as provider, health, doctor, benchmark, voice, setup, configuration, or MCP evidence; see [Issue #17](https://github.com/Capslockb/sora-agent/issues/17).

### Verification commands

```bash
sora --help
sora status --json
sora voice status
sora mcp status
python -m pytest tests/ -q
```

> These are manual verification steps until the staged pytest workflow is activated; see [Issue #12](https://github.com/Capslockb/sora-agent/issues/12). Treat `sora mcp status` as configuration/process/port diagnostics, not proof of a successful MCP handshake; see [Issue #16](https://github.com/Capslockb/sora-agent/issues/16).

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
| `sora_mcp_start` | **PARTIAL** | Start MCP over stdio. SSE and streamable HTTP are unimplemented; the separate raw WebSocket path is incomplete and unauthenticated. |
| `sora_mcp_status` | **PARTIAL** | Return configuration-, process-, and port-derived MCP diagnostics; it does not prove protocol liveness. |

Read the deep doc in [`docs/bridge-elements.md`](docs/bridge-elements.md).

---

## Feature matrix

| Feature | Status | Doc | Caveat |
|---|---|---|---|
| CLI help/version/status/doctor | **WORKING** | [`reference/cli/sora.md`](docs/reference/cli/sora.md) | — |
| Setup wizard | **PARTIAL** | [`reference/cli/setup.md`](docs/reference/cli/setup.md) | Provider coverage, reversible enablement, and ElevenLabs quick-setup mapping remain open under Issue #15. |
| Provider management | **PARTIAL** | [`guide/voice/providers.md`](docs/guide/voice/providers.md) | Setup, two CLI surfaces, and the dashboard/API do not share one canonical state; see Issue #15. |
| ElevenLabs URL signing | **WORKING** | [`guide/voice/elevenlabs.md`](docs/guide/voice/elevenlabs.md) | — |
| FastAPI dashboard | **PARTIAL** | [`reference/cli.md`](docs/reference/cli.md) | Routes run, but authentication, redaction, and safe bind defaults are unresolved. |
| Hermes plugin tools | **WORKING** | [`reference/plugins/sora-hermes.md`](docs/reference/plugins/sora-hermes.md) | Requires `discord-voice` for live audio. |
| Discord voice bridges | **PARTIAL** | [`guide/voice/gemini-live.md`](docs/guide/voice/gemini-live.md) | Live runtime in Hermes `discord-voice`. |
| VOIP Asterisk/Dograh | **PARTIAL — BLOCKED** | [`voip/setup.md`](docs/voip/setup.md) | Local startup construction is broken before PBX connection; see Issue #14. |
| MCP server | **PARTIAL** | [`guide/mcp/servers.md`](docs/guide/mcp/servers.md) | stdio is implemented; status/discovery are heuristic, network transports are incomplete or unimplemented, and the raw WebSocket path is unauthenticated. See Issue #16. |
| TUI | **PARTIAL — PROTOTYPE** | [`reference/cli/tui.md`](docs/reference/cli/tui.md) | Requires a local build and currently presents simulated or non-canonical values; see Issue #17. |
| Cron | **PLANNED** | [`reference/cli.md`](docs/reference/cli.md) | Partial. |
| Skills | **PLANNED** | [`reference/cli.md`](docs/reference/cli.md) | Partial. |
| Logs | **PLANNED** | [`reference/cli.md`](docs/reference/cli.md) | Partial. |
| Doctor auto-fix | **PLANNED** | [`reference/cli/doctor.md`](docs/reference/cli/doctor.md) | Partial. |
| ACP adapter | **RESEARCH** | [`reference/cli.md`](docs/reference/cli.md) | Stub only. |

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

The S0RA dashboard exposes control endpoints on the configured API port (default `8080`). The current API has sensitive unauthenticated read and mutation routes. Use `--host 127.0.0.1` to constrain the API listener until Issue #13 is resolved; this flag does not constrain the separately launched UI preview:

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
- **A runnable phone bridge.** The repository contains VOIP components and management surfaces, but the startup path is blocked before it can use your Asterisk PBX and Dograh gateway; see Issue #14.
- **A hosted phone service.** After the local startup path is repaired, VOIP will still require your own Asterisk PBX and Dograh gateway.
- **A complete seven-provider setup wizard.** Full setup directly configures Gemini Live and Vapi, and quick setup does not select or enable every accepted provider.
- **One unified provider-management state.** `sora setup`, `sora providers`, `sora voice providers`, and the dashboard/API do not currently share one canonical schema or command contract; see Issue #15.
- **A complete or safely exposed network MCP service.** stdio is the only implemented server transport. SSE and streamable HTTP are unimplemented, WebSocket tool calls are incomplete, and the raw listener has no authentication; see Issue #16.
- **A cloud transcription API.** S0RA can point at external Whisper endpoints, but does not host one.
- **A finished or state-backed TUI.** `sora tui` launches a locally built Ink/React prototype whose current operational panels use simulated, hard-coded, fixed, random, or display-only data; see Issue #17.
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

Expected results: CLI returns `0`, doctor reports no hard failures, API returns `{"status":"healthy"}`, tests pass. MCP status output remains diagnostic and must not be treated as proof of an authenticated or protocol-complete server session.

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
