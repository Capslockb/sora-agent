# What is S0RA?

**S0RA Agent** is a Hermes-aligned voice companion CLI. It focuses on real-time voice AI through multiple providers, but it does **not** reimplement the live Discord audio path — that is provided by the Hermes `discord-voice` plugin. S0RA supplies the operator layer: setup, status, provider management, sidecar API, and Hermes plugin tools.

## Supported providers (configuration + status)

These providers can be configured, enabled, and queried from S0RA. Live audio requires the appropriate runtime. The checked-in VOIP entrypoints are additionally blocked by local construction errors before they can reach Asterisk or Dograh; see [Issue #14](https://github.com/Capslockb/sora-agent/issues/14).

- **Gemini Live** — Google's multimodal live API (Discord + VOIP) — **PARTIAL**
- **Vapi.ai** — Managed conversational AI platform (Discord + Phone) — **PARTIAL**
- **ElevenLabs** — High-quality conversational AI (Discord) — **WORKING** for URL signing, **PARTIAL** for live bridge
- **OpenAI Realtime** — WebRTC-based realtime voice — **PARTIAL**
- **xAI Grok** — Real-time voice via Grok models — **PARTIAL**
- **Ultravox** — Managed STT/LLM/TTS pipeline — **PARTIAL**
- **Retell AI** — Voice agent platform — **PARTIAL**
- **Edge TTS / OpenAI TTS / Whisper** — TTS/STT fallback providers — **WORKING** for enable/disable

## Key philosophy

| Aspect | Approach | Status |
|---|---|---|
| Architecture | Mirrors Hermes constants/config/logging/profiles | **WORKING** |
| Distribution | `pipx install git+https://...` | **WORKING** |
| Provider toggle | Enable/disable TTS/STT/LLM-voice at runtime | **WORKING** |
| VOIP | Intended Asterisk ARI + Dograh path | **PARTIAL — BLOCKED**: both startup entrypoints fail during local bridge construction before PBX connection; see Issue #14 |
| MCP | stdio server; HTTP/SSE/WebSocket scaffolding | **PARTIAL** |
| Memory | Honcho / Hermes passthrough detection | **PARTIAL** |
| Web dashboard | FastAPI dashboard and control API, port 8080 | **PARTIAL** — routes run, but authentication, secret redaction, constrained CORS, and a safe bind default are unresolved |
| TUI | Planned Ink/React interface | **PLANNED** |

> The dashboard currently defaults to all interfaces and exposes sensitive unauthenticated routes. Keep it bound to `127.0.0.1` and do not publish it to a LAN, tunnel, container host interface, or the internet; see [Issue #13](https://github.com/Capslockb/sora-agent/issues/13).

## Quick comparison

| Feature | Hermes | S0RA |
|---|---|---|
| Primary interface | Text chat | **CLI + sidecar API** |
| Discord voice runtime | `discord-voice` plugin | Same `discord-voice` plugin (S0RA configures it) |
| Provider toggle | No | **Yes — WORKING** |
| MCP | Yes | stdio **WORKING**, WebSocket/HTTP **PARTIAL** |
| Web dashboard | No | **Yes — PARTIAL**; loopback-only until the control API is authenticated and secrets are redacted |
| TUI | No | **PLANNED** |
| ACP server | No | **RESEARCH** |

## Who is it for?

- Hermes users who want a dedicated CLI for voice/provider configuration.
- Self-hosters evaluating an Asterisk + Dograh phone bridge after the startup blocker in Issue #14 is resolved.
- Anyone building a companion agent layer that shares Hermes conventions.

Read the full status table in [`release-readiness.md`](../release-readiness.md).
