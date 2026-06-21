# Release Readiness

This page collects the current truth table, release-blocking rules, and the end-to-end smoke checklist for S0RA Agent.

## Status legend

| Label | Meaning |
|---|---|
| **WORKING** | Code exists and has a runnable verification path in this repo. |
| **PARTIAL** | Code exists but requires external credentials, services, or another plugin/runtime. |
| **PLANNED** | Entry points or scaffolding exist, but the core feature is not implemented. |
| **RESEARCH** | Future integration target; no production code yet. |

## Hard release rules

1. **No false claims.** Every feature in README and docs uses one of the four labels above.
2. **Every `WORKING` feature must have a verification command.** Prefer commands that run without external API keys.
3. **Every `PARTIAL` feature must state the missing runtime.** Example: Discord voice bridges require the Hermes `discord-voice` plugin.
4. **No screenshots of unreleased UIs.** The TUI is `PLANNED`; do not show it as shipped.
5. **API routes must match code.** The sidecar API table is generated from `sora_api.py`.
6. **Docs-site must build without dead links.** Run `npm run docs:build` before release.

## Truth table

| Area | Status | Evidence / caveat |
|---|---|---|
| CLI entry (`sora --help`, `sora status`, `sora doctor`) | **WORKING** | `tests/test_cli.py`, manual run |
| Setup wizard (`sora setup`) | **WORKING** | `sora_cli/setup.py` interactive flow |
| Provider registry (`sora voice providers list/enable/disable`) | **WORKING** | `sora_cli/voice.py` provider commands |
| ElevenLabs signed URLs / WebSocket targets | **WORKING** | `sora_cli/voice.py` URL signing helpers |
| FastAPI dashboard (`/health`, `/api/status`) | **WORKING** | `sora_api.py`, verified with `TestClient` |
| Hermes plugin (`sora-hermes`) | **WORKING** | `plugins/sora_hermes/plugin.yaml`, registers 6 tools |
| Discord voice bridges (`sora voice live/vapi/…`) | **PARTIAL** | CLI prepares bridge; live audio via Hermes `discord-voice` |
| MCP server management (`sora mcp start/status/catalog`) | **PARTIAL** | stdio supported; SSE/WebSocket scaffolding |
| VOIP Asterisk + Dograh (`sora-voip`) | **PARTIAL** | Plugin exists; requires Asterisk/Dograh PBX |
| TUI mode (`sora tui`) | **PLANNED** | `sora_cli/tui.py` is a stub/repl |
| Cron job management (`sora cron`) | **PLANNED** | Commands exist; create/run not implemented |
| Skill management (`sora skills`) | **PLANNED** | Commands exist; operations not implemented |
| Log filtering (`sora logs`) | **PLANNED** | View works; filtering not implemented |
| Doctor auto-fix (`sora doctor --fix`) | **PLANNED** | Diagnostics work; auto-fix stub |
| ACP adapter (`sora acp`) | **RESEARCH** | Entry point stub only |

## E2E smoke checklist

Run these before tagging a release:

```bash
# CLI smoke
sora --help
sora --version
sora status
sora doctor

# Voice/MCP smoke (no external keys needed)
sora voice providers list
sora mcp catalog

# API smoke (start the dashboard in another terminal)
curl -s http://127.0.0.1:8080/health

# Test suite
python -m pytest tests/ -q

# Hermes plugin smoke (when Hermes is installed)
hermes plugins enable sora-hermes
hermes tools list | grep sora_
```

## Release-blocking gaps

| Gap | Severity | Next step |
|---|---|---|
| TUI is a stub | Medium | Decide whether to implement or hide behind `PLANNED` |
| `sora voice live` cannot start live audio without Hermes `discord-voice` | Medium | Document clearly as `PARTIAL`; add setup guide |
| `sora mcp start` HTTP/SSE not wired | Medium | Downgrade docs or implement transport selection |
| `sora doctor --fix` not implemented | Low | Document as `PLANNED` |
| `sora acp` is a stub | Low | Document as `RESEARCH` |
| VOIP docs need a live PBX example | Medium | Add an asterisk/docker example or mark `PARTIAL` |

## Anti-claims

S0RA does **not** currently ship:

- A self-contained live Discord voice bridge (runtime is Hermes `discord-voice`).
- A hosted VOIP service.
- A production TUI.
- A production ACP server.
- Auto-fix diagnostics.

## Release tag note

When these docs are merged, bump `version` in `pyproject.toml` and `sora_api.py`, update `CHANGELOG.md`, and run:

```bash
npm run docs:build
python -m pytest tests/ -q
```
