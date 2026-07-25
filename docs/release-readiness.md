# Release Readiness

This page collects the current truth table, release-blocking rules, and the end-to-end smoke checklist for S0RA Agent.

## Status legend

| Label | Meaning |
|---|---|
| **WORKING** | Code exists and has a runnable verification path in this repo. |
| **PARTIAL** | Code exists but requires external credentials, services, another plugin/runtime, or has a material safety or lifecycle boundary. |
| **PLANNED** | Entry points or scaffolding exist, but the core feature is not implemented. |
| **RESEARCH** | Future integration target; no production code yet. |

## Hard release rules

1. **No false claims.** Every feature in README and docs uses one of the four labels above.
2. **Every `WORKING` feature must have a verification command.** Prefer commands that run without external API keys.
3. **Every `PARTIAL` feature must state the missing runtime, lifecycle, or safety boundary.** Example: Discord voice bridges require the external Hermes voice runtime.
4. **No screenshots of unreleased UIs.** The TUI is `PLANNED`; do not show it as shipped.
5. **API documentation must match `sora_api.py`.** The route tables are maintained manually and must be rechecked against source; they are not generated automatically.
6. **Docs-site must build without dead links.** Run `npm run docs:build` before release.
7. **Local test results are not CI evidence.** Until [Issue #12](https://github.com/Capslockb/sora-agent/issues/12) is completed, describe pytest results as locally verified and do not imply that GitHub Actions validates the current head.
8. **Do not present the dashboard as network-safe.** Until [Issue #13](https://github.com/Capslockb/sora-agent/issues/13) is resolved, document it as an unauthenticated trusted-local-development surface.
9. **Do not present VOIP startup as runnable.** Until [Issue #14](https://github.com/Capslockb/sora-agent/issues/14) is resolved, distinguish management/configuration command surfaces from a working bridge lifecycle.

## Current validation boundary

PR #5 recorded **24/24 tests passing locally** before it was merged. That result covers the tested PR state, but it is not exact-head CI evidence for later commits on `main`. The pytest workflow is still staged at `ci/tests.yml`, where GitHub Actions will not execute it; activation is tracked in [Issue #12](https://github.com/Capslockb/sora-agent/issues/12).

Documentation-only commits after PR #5 have no attached Actions evidence. Runtime or security claims must therefore be verified from current source and should not be described as CI-proven.

## Truth table

| Area | Status | Evidence / caveat |
|---|---|---|
| CLI entry (`sora --help`, `sora status`, `sora doctor`) | **WORKING** | `tests/test_cli.py`, manual run |
| Setup wizard (`sora setup`) | **WORKING** | `sora_cli/setup.py` interactive flow |
| Provider registry (`sora voice providers list/enable/disable`) | **WORKING** | `sora_cli/voice.py` provider commands |
| ElevenLabs signed URLs / WebSocket targets | **WORKING** | `sora_cli/voice.py` URL signing helpers |
| FastAPI dashboard (`/health`, `/api/status`) | **PARTIAL** | Routes run, but the API defaults to `0.0.0.0`, has no authentication, broad CORS, and sensitive config/env routes; see Issue #13 |
| Hermes plugin (`sora-hermes`) | **WORKING** | `plugins/sora_hermes/plugin.yaml`; six registered tools |
| Discord voice bridges (`sora voice live/vapi/…`) | **PARTIAL** | CLI prepares bridge state; live audio requires the external Hermes voice runtime |
| MCP server management (`sora mcp start/status/catalog`) | **PARTIAL** | stdio CLI path exists; HTTP/SSE/WebSocket control remains scaffolded or configuration-only |
| VOIP Asterisk + Dograh (`sora-voip`) | **PARTIAL** | Management/configuration surfaces exist, but `sora voip start` and `sora-voip-bridge` import a nonexistent `VoipConfig` and do not match the current `VoipBridge` constructor; external PBX work and Issue #7 also remain; see Issue #14 |
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

# API smoke — bind or firewall the API for loopback-only use
curl -s http://127.0.0.1:8080/health

# Test suite
python -m pytest tests/ -q

# Hermes plugin smoke (when Hermes is installed)
hermes plugins enable sora-hermes
hermes tools list | grep sora_
```

Do not use `/api/config`, `/api/config/env`, or mutation routes as routine release smoke tests while Issue #13 remains open.

Do not add `sora voip start` or `sora-voip-bridge` to the release smoke checklist until Issue #14 is fixed and exact-head lifecycle validation passes.

## Release-blocking gaps

| Gap | Severity | Next step |
|---|---|---|
| Dashboard API is unauthenticated, defaults to all interfaces, and can return secret values | **High** | Complete [Issue #13](https://github.com/Capslockb/sora-agent/issues/13) with exact-head security tests |
| VOIP entrypoints cannot construct the checked-in bridge runtime | **High** | Complete [Issue #14](https://github.com/Capslockb/sora-agent/issues/14) through a focused, separately reviewed lifecycle PR |
| CLI secret handling and nondeterministic local execution remain open | **High** | Complete [Issue #7](https://github.com/Capslockb/sora-agent/issues/7) |
| Pytest workflow is staged but inactive | Medium | Complete [Issue #12](https://github.com/Capslockb/sora-agent/issues/12), then attach the first exact-head Actions result |
| TUI is a stub | Medium | Decide whether to implement or keep clearly labeled `PLANNED` |
| `sora voice live` cannot start live audio without the external Hermes voice runtime | Medium | Keep documented as `PARTIAL`; add verified runtime setup guidance |
| `sora mcp start` HTTP/SSE/WebSocket paths are not supervised runtimes | Medium | Downgrade claims or implement transport lifecycle |
| `sora doctor --fix` not implemented | Low | Keep documented as `PLANNED` |
| `sora acp` is a stub | Low | Keep documented as `RESEARCH` |
| VOIP docs need a live PBX example after the local startup path is repaired | Medium | First complete Issue #14, then add a validated Asterisk/Dograh example |

## Anti-claims

S0RA does **not** currently ship:

- A self-contained live Discord voice bridge.
- A currently runnable end-to-end VOIP bridge entrypoint.
- A hosted VOIP service.
- A secured network dashboard/control API.
- A production TUI.
- A production ACP server.
- Auto-fix diagnostics.

## Release tag note

A documentation change alone does not require a version bump. Version, changelog, and release-tag changes are separate owner decisions and must be validated as release work.

Before an actual release, run:

```bash
npm run docs:build
python -m pytest tests/ -q
```

Treat those commands as local evidence until Issue #12 activates CI.
