# What is S0RA?

**S0RA Agent** is a standalone CLI application that mirrors the Hermes Agent architecture but focuses on **real-time voice AI** through multiple providers (7 bridges + 6 TTS/STT):

- **Gemini Live** — Google's multimodal live API (Discord + VOIP)
- **Vapi.ai** — Managed conversational AI platform (Discord + Phone)
- **ElevenLabs** — High-quality conversational AI (Discord)
- **OpenAI Realtime** — WebRTC-based realtime voice with function calling
- **xAI Grok** — Real-time voice via Grok models (WSS)
- **Ultravox** — Managed STT/LLM/TTS pipeline
- **Retell AI** — Voice agent platform for telephony/web calls
- **Edge TTS / OpenAI TTS / Whisper** — Local/cloud TTS & STT fallback

## Key Philosophy

| Aspect | Approach |
|--------|----------|
| **Architecture** | Mirrors Hermes exactly (constants, config, logging, profiles, skins, plugins) |
| **Distribution** | `pipx install git+https://...` — isolated, updatable, git-based |
| **Voice** | Provider toggle: switch TTS/STT/LLM Voice at runtime |
| **VOIP** | Asterisk ARI → RTP → Dograh → Gemini Live (phone calls, not Discord) |
| **MCP** | Auto-discovers local MCP servers (stdio + HTTP 3000-3010) |
| **Memory** | Detects Honcho, OpenClaw, Hermes memory — auto-configures passthrough |
| **Extensibility** | Plugin system compatible with Hermes plugins |
| **UI** | CLI + TUI (Ink/React) + Web Dashboard (React/Vite) |

## Quick Comparison

| Feature | Hermes | S0RA |
|---------|--------|------|
| Primary Interface | Text chat | **Voice-first** (Discord + VOIP) |
| Voice Providers | Discord only | Discord + **Asterisk/SIP + Dograh** |
| Provider Toggle | No | **Yes** (Gemini/Vapi/ElevenLabs/OpenAI/xAI/Ultravox/Retell/Edge/OpenAI/Whisper) |
| MCP | Yes | Yes + **auto-discovery + WebSocket** |
| Installation | `pipx install hermes-agent` | `pipx install git+...sora-agent` |
| Updates | Git-based | **Git-based** |
| Web Dashboard | No | **Yes** (live demo, provider toggles) |
| TUI | No | **Yes** (Ink/React) |
| ACP Server | No | **Yes** |

## Who Is It For?

- **Self-hosters** with Asterisk + Dograh wanting phone-call AI
- **Discord bot developers** needing multi-provider voice bridges
- **Hermes users** wanting a voice-focused companion agent
- **Anyone** wanting a `hermes`-like CLI for voice AI that works standalone