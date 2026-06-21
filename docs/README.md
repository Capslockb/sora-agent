# S0RA Agent Docs

This is the raw documentation tree for S0RA Agent. The VitePress site under `docs/.vitepress/` builds the public docs from these files.

## Status legend

Every feature in S0RA is tagged with one of four truth labels:

| Label | Meaning |
|---|---|
| **WORKING** | Code exists in the repo and has a runnable verification path. |
| **PARTIAL** | Code exists but depends on external services, credentials, another plugin, or runtime wiring. |
| **PLANNED** | Entry points or scaffolding exist, but the core functionality is not implemented. |
| **RESEARCH** | Mentioned as a future integration target; no production code yet. |

## Documentation index

| Doc | Purpose |
|---|---|
| [`guide/quick-start.md`](guide/quick-start.md) | Install, first commands, verify, pitfalls, next steps |
| [`guide/architecture.md`](guide/architecture.md) | System map, audio paths, integration boundaries, key files |
| [`guide/voice/providers.md`](guide/voice/providers.md) | Provider enable/disable and runtime knobs |
| [`guide/voice/gemini-live.md`](guide/voice/gemini-live.md) | Gemini Live Discord bridge |
| [`guide/mcp/servers.md`](guide/mcp/servers.md) | MCP server management |
| [`voip/setup.md`](voip/setup.md) | Asterisk + Dograh VOIP setup |
| [`bridge-elements.md`](bridge-elements.md) | S0RA operator tools and sidecar API |
| [`env-vars.md`](env-vars.md) | Exhaustive environment variable reference |
| [`release-readiness.md`](release-readiness.md) | Truth table, hard release rules, smoke checklist, gaps |
| [`troubleshooting.md`](troubleshooting.md) | Common failures, log locations, fixes |

## Quick verification

```bash
sora --help
sora doctor
sora status
python -m pytest tests/ -q
```

For the project overview, see the top-level [`README.md`](../README.md).
