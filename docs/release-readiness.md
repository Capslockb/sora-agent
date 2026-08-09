# Release Readiness

This page collects the current truth table, release-blocking rules, and the end-to-end smoke checklist for S0RA Agent.

## Status legend

| Label | Meaning |
|---|---|
| **WORKING** | Code exists and has a runnable verification path in this repo. |
| **PARTIAL** | Code exists but requires external credentials, services, another plugin/runtime, or has a material safety, state, or lifecycle boundary. |
| **PLANNED** | Entry points or scaffolding exist, but the core feature is not implemented. |
| **RESEARCH** | Future integration target; no production code yet. |

## Hard release rules

1. **No false claims.** Every feature in README and docs uses one of the four labels above.
2. **Every `WORKING` feature must have a verification command.** Prefer commands that run without external API keys.
3. **Every `PARTIAL` feature must state the missing runtime, lifecycle, state, or safety boundary.** Example: Discord voice bridges require the external Hermes voice runtime.
4. **Do not present prototype UI output as live evidence.** Until [Issue #17](https://github.com/Capslockb/sora-agent/issues/17) is resolved, TUI screenshots and demonstrations must visibly retain the prototype boundary and must not imply that simulated provider, voice, health, doctor, benchmark, setup, configuration, or MCP values came from live state.
5. **API documentation must match `sora_api.py`.** The route tables are maintained manually and must be rechecked against source; they are not generated automatically.
6. **The docs-site build must succeed, but build success is not dead-link evidence.** VitePress currently sets `ignoreDeadLinks: true`, so `npm --prefix docs ci && npm --prefix docs run docs:build` verifies the site build but does not prove that links are valid. Dead-link validation requires a separate check or an explicitly reviewed configuration change.
7. **Do not confuse local pytest with Actions evidence.** Until [Issue #12](https://github.com/Capslockb/sora-agent/issues/12) is completed on `main`, locally run pytest remains local evidence. An exact PR head may be described as Actions-validated only when a `Tests` run is attached to that head; draft PR #25 is the current exception, and its passing PR-level run does not activate pytest CI on `main` or other branches.
8. **Do not present the dashboard as network-safe.** Until [Issue #13](https://github.com/Capslockb/sora-agent/issues/13) is resolved, document it as an unauthenticated trusted-local-development surface.
9. **Do not present VOIP startup as runnable.** Until [Issue #14](https://github.com/Capslockb/sora-agent/issues/14) is resolved, distinguish management/configuration command surfaces from a working bridge lifecycle.
10. **Do not present setup or provider management as one reliable control surface.** Until [Issue #15](https://github.com/Capslockb/sora-agent/issues/15) is resolved, distinguish `sora setup`, `sora setup --provider`, `sora providers`, `sora voice providers`, and the dashboard/API. Quick setup mainly stores credential or identifier values; it does not prove selection, enablement, reachability, or agreement with another surface.
11. **Do not present MCP network transports or discovery as operational.** Until [Issue #16](https://github.com/Capslockb/sora-agent/issues/16) is resolved, state that `sora mcp start` implements stdio only, the custom WebSocket path is incomplete and unauthenticated, and setup/status detection is heuristic rather than protocol-verified.
12. **Do not present `sora update` as a general installation upgrader.** Until [Issue #18](https://github.com/Capslockb/sora-agent/issues/18) is resolved, mark it `PARTIAL`, limit its documented use to independently verified compatible Git checkouts, warn that it lacks safe worktree/branch/remote preflight, and direct pipx VCS users to reinstall from the same repository URL.
13. **Do not claim required-check or code-owner enforcement that repository settings do not provide.** Until [Issue #20](https://github.com/Capslockb/sora-agent/issues/20) is resolved, do not describe `public-docs-safety` or CODEOWNERS review as required or enforced on `main`.

## Current validation boundary

PR #5 recorded **24/24 tests passing locally** before it was merged. That result covers the tested PR state, but it is not exact-head CI evidence for later commits on `main`. On current `main`, the pytest workflow is still staged at `ci/tests.yml`, where GitHub Actions will not execute it; activation is tracked in [Issue #12](https://github.com/Capslockb/sora-agent/issues/12).

Draft PR #25 is the current exception to that branch-wide boundary: its exact head activates `.github/workflows/tests.yml` and has a successful PR-level `Tests` run on Python 3.12 and 3.13. That evidence applies only to PR #25's exact head; it does not activate pytest CI on `main` or prove later unrelated heads.

The repository has a separate Pages workflow at `.github/workflows/docs.yml` that builds the VitePress site from `docs/` on pushes to `main`. That deployment workflow does not validate Python runtime or security changes.

Documentation-only commits after PR #5 have no attached pytest Actions evidence. PR #25 is not documentation-only; its exact-head `Tests` run proves only that CI-activation branch. Runtime or security claims on `main` or other PR heads must therefore be verified from current source and should not be described as CI-proven without their own exact-head evidence.

## Truth table

| Area | Status | Evidence / caveat |
|---|---|---|
| CLI entry (`sora --help`, `sora status`, `sora doctor`) | **WORKING** | `sora_cli/main.py`, `sora_cli/doctor.py`; release smoke commands |
| Setup wizard (`sora setup`, `sora setup --provider`) | **PARTIAL** | The full voice section directly configures only Gemini Live and Vapi, declining enable prompts does not clear existing enabled state, quick paths do not select or enable providers, and the ElevenLabs quick path does not collect `ELEVENLABS_API_KEY`; see Issue #15. |
| Provider management (`sora providers`, `sora voice providers`) | **PARTIAL** | The two command families use different registries, configuration paths, provider coverage, and disable semantics. Setup and the dashboard/API add more state shapes; see Issue #15. |
| `sora update` | **PARTIAL** | Normal pipx VCS installs are not Git checkouts, while source-checkout updates hard-code `origin/main`, require undeclared `uv`, and do not preflight dirty, detached, divergent, remapped, or non-`main` states; see Issue #18. |
| ElevenLabs signed URLs / WebSocket targets | **WORKING** | `sora_cli/voice.py` URL signing helpers |
| FastAPI dashboard (`/health`, `/api/status`) | **PARTIAL** | Routes run, but the API defaults to `0.0.0.0`, has no authentication, broad CORS, and sensitive config/env routes; see Issue #13 |
| Hermes plugin (`sora-hermes`) | **WORKING** | `plugins/sora_hermes/plugin.yaml`; six registered tools |
| Discord voice bridges (`sora voice live/vapi/…`) | **PARTIAL** | CLI prepares bridge state; live audio requires the external Hermes voice runtime |
| MCP server management (`sora mcp`) | **PARTIAL** | The built-in server implements stdio only. SSE and streamable HTTP raise `NotImplementedError`; the custom WebSocket path is unauthenticated, incomplete, and cannot complete tool calls as written. Setup/status detection uses unverified port/process heuristics; see Issue #16. |
| VOIP Asterisk + Dograh (`sora-voip`) | **PARTIAL** | Management/configuration surfaces exist, but `sora voip start` and the installed `sora-voip` entrypoint import a nonexistent `VoipConfig` and do not match the current `VoipBridge` constructor. The standalone implementation also contains stale `sora-voip-bridge` help examples for a console script that `pyproject.toml` does not expose. External PBX work and Issue #7 also remain; see Issue #14 |
| TUI mode (`sora tui`) | **PARTIAL — PROTOTYPE** | The checked-in Ink/React application requires a local build. Its voice, status, provider, doctor, benchmark, setup, configuration, and MCP panels currently use simulated, hard-coded, fixed, random, or display-only data rather than canonical live state; see Issue #17. |
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

# Provider and MCP diagnostics (no external keys needed)
sora providers list
sora voice providers list
sora mcp catalog
sora mcp status

# API smoke — bind or firewall the API for loopback-only use
curl -s http://127.0.0.1:8080/health

# Test suite
python -m pytest tests/ -q

# Documentation site (run from the repository root)
npm --prefix docs ci
npm --prefix docs run docs:build

# Hermes plugin smoke (when Hermes is installed)
hermes plugins enable sora-hermes
hermes tools list | grep sora_
```

The setup and provider commands are diagnostics while Issue #15 remains open. Differences between their stored or reported state are evidence of the known split, not proof that one view is canonical. Keep sensitive values out of release evidence.

`sora mcp catalog` is static metadata and `sora mcp status` uses listener/process heuristics. Neither proves an MCP transport or tool server is healthy. Do not add SSE, streamable HTTP, or the custom WebSocket listener to release smoke checks until Issue #16 is resolved and exact-head lifecycle/security validation passes.

Do not use `/api/config`, `/api/config/env`, or mutation routes as routine release smoke tests while Issue #13 remains open.

Do not add `sora voip start` or `sora-voip` to the release smoke checklist until Issue #14 is fixed and exact-head lifecycle tests pass.

Do not add `sora update` to release smoke checks or general upgrade instructions until Issue #18 is fixed and exact-head installation/lifecycle tests cover pipx VCS installs and safe Git-checkout updates.

## Release-blocking gaps

| Gap | Severity | Next step |
|---|---|---|
| Dashboard API is unauthenticated, defaults to all interfaces, and can return secret values | **High** | Complete [Issue #13](https://github.com/Capslockb/sora-agent/issues/13) with exact-head security tests |
| VOIP entrypoints cannot construct the checked-in bridge runtime | **High** | Complete [Issue #14](https://github.com/Capslockb/sora-agent/issues/14) through a focused, separately reviewed lifecycle PR |
| CLI secret handling and nondeterministic local execution remain open | **High** | Complete [Issue #7](https://github.com/Capslockb/sora-agent/issues/7) |
| Setup quick paths and provider controls do not share truthful selection or credential semantics | **High** | Complete [Issue #15](https://github.com/Capslockb/sora-agent/issues/15), including the ElevenLabs variable mapping and reversible enable/disable behavior |
| MCP network transports and discovery are incomplete, unauthenticated, or heuristic | **High** | Complete [Issue #16](https://github.com/Capslockb/sora-agent/issues/16) through a focused transport/discovery PR with exact-head tests |
| Pytest workflow is staged but inactive on `main` | Medium | Complete [Issue #12](https://github.com/Capslockb/sora-agent/issues/12), then attach the first exact-head post-merge Actions result |
| `public-docs-safety` and code-owner review are not enforced on `main` | Medium | Complete [Issue #20](https://github.com/Capslockb/sora-agent/issues/20) by enabling and verifying the intended branch/ruleset requirements |
| TUI build/runtime contract is inconsistent and operational panels are simulated | Medium | Complete [Issue #17](https://github.com/Capslockb/sora-agent/issues/17) through one focused build/runtime PR with deterministic tests |
| `sora update` is unavailable for normal pipx VCS installs and can mutate a source checkout without safe preflight | Medium | Complete [Issue #18](https://github.com/Capslockb/sora-agent/issues/18) through a focused installation/lifecycle PR with deterministic exact-head tests |
| `sora voice live` cannot start live audio without the external Hermes voice runtime | Medium | Keep documented as `PARTIAL`; add verified runtime setup guidance |
| `sora doctor --fix` not implemented | Low | Keep documented as `PLANNED` |
| `sora acp` is a stub | Low | Keep documented as `RESEARCH` |
| VOIP docs need a live PBX example after the local startup path is repaired | Medium | First complete Issue #14, then add a validated Asterisk/Dograh example |

## Anti-claims

S0RA does **not** currently ship:

- A self-contained live Discord voice bridge.
- A currently runnable end-to-end VOIP bridge entrypoint.
- A hosted VOIP service.
- A secured network dashboard/control API.
- A production SSE, streamable-HTTP, or WebSocket MCP server.
- Protocol-verified MCP auto-discovery or supervised lifecycle management for saved MCP commands.
- A complete seven-provider setup wizard or a quick path that selects and enables every accepted provider.
- One unified, authoritative provider-management state across setup, both CLI command families, and the dashboard/API.
- A safe installation-aware general updater for pipx and arbitrary source checkouts.
- A production TUI.
- A production ACP server.
- Auto-fix diagnostics.

## Release tag note

A documentation change alone does not require a version bump. Version, changelog, and release-tag changes are separate owner decisions and must be validated as release work.

Before an actual release, run from the repository root:

```bash
npm --prefix docs ci
npm --prefix docs run docs:build
python -m pytest tests/ -q
```

Treat those commands as local evidence on any head without an attached `Tests` workflow. Until Issue #12 is merged and revalidated, `main` still lacks repository-wide pytest CI.
