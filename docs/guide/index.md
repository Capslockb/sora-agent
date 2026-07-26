# What is S0RA?

**S0RA Agent** is a Hermes-aligned voice companion CLI. It focuses on real-time voice AI through multiple providers, but it does **not** reimplement the live Discord audio path — that is provided by the Hermes `discord-voice` plugin. S0RA supplies the operator layer: setup, status, provider management, sidecar API, and Hermes plugin tools.

## Supported providers (configuration + status)

S0RA contains preparation and configuration paths for the providers below. Provider management is currently **PARTIAL** because `sora providers` and `sora voice providers` use different registries, configuration shapes, provider coverage, and disable semantics; the dashboard/API reads another selection shape. Use `sora setup` for initial configuration and treat provider-command results as diagnostic until [Issue #15](https://github.com/Capslockb/sora-agent/issues/15) is resolved. Live audio also requires the appropriate runtime. The checked-in VOIP entrypoints are additionally blocked by local construction errors before they can reach Asterisk or Dograh; see [Issue #14](https://github.com/Capslockb/sora-agent/issues/14).

- **Gemini Live** — Google's multimodal live API (Discord + VOIP) — **PARTIAL**
- **Vapi.ai** — Managed conversational AI platform (Discord + Phone) — **PARTIAL**
- **ElevenLabs** — High-quality conversational AI (Discord) — **WORKING** for URL signing, **PARTIAL** for live bridge
- **OpenAI Realtime** — WebRTC-based realtime voice — **PARTIAL**
- **xAI Grok** — Real-time voice via Grok models — **PARTIAL**
- **Ultravox** — Managed STT/LLM/TTS pipeline — **PARTIAL**
- **Retell AI** — Voice agent platform — **PARTIAL**
- **Edge TTS / OpenAI TTS / Whisper** — TTS/STT fallback definitions — **PARTIAL** through the split provider-management surfaces

## Key philosophy

| Aspect | Approach | Status |
|---|---|---|
| Architecture | Mirrors Hermes constants/config/logging/profiles | **WORKING** |
| Distribution | `pipx install git+https://...` | **WORKING** |
| Provider management | Configure with `sora setup`; inspect or mutate through two divergent CLI surfaces | **PARTIAL** — not one authoritative state model; see Issue #15 |
| VOIP | Intended Asterisk ARI + Dograh path | **PARTIAL — BLOCKED**: both startup entrypoints fail during local bridge construction before PBX connection; see Issue #14 |
| MCP | stdio server plus incomplete or unimplemented network paths | **PARTIAL** — SSE and streamable HTTP are unimplemented; the separate raw WebSocket listener is incomplete and unauthenticated; see Issue #16 |
| Memory | Honcho / Hermes passthrough detection | **PARTIAL** |
| Web dashboard | FastAPI dashboard and control API, port 8080 | **PARTIAL** — routes run, but authentication, secret redaction, constrained CORS, and safe defaults for both listeners are unresolved |
| TUI | Locally built Ink/React prototype | **PARTIAL — PROTOTYPE** — operational panels use simulated, hard-coded, fixed, random, or display-only data; see Issue #17 |

> The dashboard control API defaults to all interfaces, while `--host` does not constrain the separately launched UI preview. Treat the whole dashboard as a trusted-local-development surface: do not run it on a shared or network-reachable host, and do not publish either listener through a LAN, tunnel, container port, reverse proxy, or the internet. See [Issue #13](https://github.com/Capslockb/sora-agent/issues/13).

> The TUI is not a live management surface. Do not use its output as provider, health, doctor, benchmark, voice, setup, configuration, or MCP evidence until the runtime and deterministic-build blockers in [Issue #17](https://github.com/Capslockb/sora-agent/issues/17) are resolved.

## Quick comparison

| Feature | Hermes | S0RA |
|---|---|---|
| Primary interface | Text chat | **CLI + sidecar API** |
| Discord voice runtime | `discord-voice` plugin | Same `discord-voice` plugin (S0RA configures it) |
| Provider management | No | **Yes — PARTIAL**; two command families and the dashboard/API do not yet share one canonical state |
| MCP | Yes | stdio **WORKING**; SSE and streamable HTTP unimplemented; raw WebSocket path incomplete and unauthenticated |
| Web dashboard | No | **Yes — PARTIAL**; trusted-local-development only until both listeners are constrained and the control API is authenticated and redacted |
| TUI | No | **PARTIAL — PROTOTYPE**; locally built and currently simulated/non-canonical |
| ACP server | No | **RESEARCH** |

## Who is it for?

- Hermes users who want a dedicated CLI for voice/provider configuration and can work within the current provider-state limitation.
- Self-hosters evaluating an Asterisk + Dograh phone bridge after the startup blocker in Issue #14 is resolved.
- Anyone building a companion agent layer that shares Hermes conventions.

Read the full status table in [`release-readiness.md`](../release-readiness.md).