---
layout: home
hero:
  name: S0RA Agent
  text: Hermes Voice Companion CLI
  tagline: Built around Gemini Live, Vapi, ElevenLabs, OpenAI Realtime, xAI Grok, Ultravox, Retell AI, and VOIP (Asterisk + Dograh). Designed as a Hermes companion layer, not a separate isolated chat brain.
  image:
    src: /sora-agent/favicon.svg
    alt: S0RA Agent
  actions:
    - theme: brand
      text: Quick Start
      link: /guide/quick-start
    - theme: alt
      text: GitHub Repo
      link: https://github.com/Capslockb/sora-agent

features:
  - icon: 🎙️
    title: Multi-Provider Voice
    details: Provider adapters and CLI surfaces exist for multiple backends, but setup, provider commands, and the dashboard do not yet share one canonical selection state. See Issue #15 before treating them as interchangeable controls.
  - icon: 📞
    title: VOIP / Asterisk + Dograh
    details: Intended self-hosted PBX architecture using Asterisk ARI and Dograh. The checked-in VOIP startup entrypoints are currently blocked before they can construct the bridge runtime; see Issue #14.
  - icon: 🔌
    title: MCP Integration
    details: stdio management paths exist. HTTP, SSE, and WebSocket lifecycle claims remain partial or scaffolded and require exact-runtime validation.
  - icon: 🎨
    title: Hermes DNA
    details: Companion configuration, plugin, constants, and logging patterns aligned with Hermes rather than a separate isolated assistant runtime.
  - icon: 🌐
    title: Voice Visualizer Web UI
    details: React + Vite visualizer and a FastAPI control surface. The current API is unauthenticated and the separately launched UI preview has no explicit bind-host control; keep both local-only under Issue #13.
  - icon: 📦
    title: Install Anywhere
    details: pipx install git+https://github.com/Capslockb/sora-agent. Setup is interactive and partial for provider selection; OpenWakeWord installation is optional.
  - icon: 🩺
    title: Doctor & Benchmark
    details: Diagnostic and benchmark commands exist. Doctor auto-fix is a stub, local benchmark execution remains under Issue #7, and current main has no active pytest workflow.
  - icon: 🤖
    title: ACP Adapter
    details: Research-stage entrypoint only. Do not present it as a production ACP server or full editor integration.
---

<div class="vp-doc" style="text-align: center; margin-top: 2rem;">

## Install Now

```bash
# Via pipx (recommended)
pipx install git+https://github.com/Capslockb/sora-agent

# Or clone & install
git clone https://github.com/Capslockb/sora-agent
cd sora-agent
pip install -e .
```

## First Commands

```bash
sora setup              # Partial interactive setup; see Issue #15
sora status             # Local configuration/dependency snapshot
sora providers list     # Diagnostic provider view
sora voice providers list  # Separate diagnostic provider view
sora voice live         # Prepare Gemini Live bridge; external Hermes runtime required
sora voice vapi         # Prepare Vapi bridge; external Hermes runtime required
sora mcp catalog        # Inspect MCP catalog
sora voice voip-status  # Bridge-dependent status; VOIP startup is blocked
sora doctor             # Diagnostics; --fix is not implemented
sora tui                # Planned stub that falls back to the REPL
```

The full setup wizard directly configures Gemini Live and Vapi only. `sora setup --provider` mainly stores credentials or identifiers and does not prove selection or enablement; the current ElevenLabs quick path does not collect `ELEVENLABS_API_KEY`. See [Issue #15](https://github.com/Capslockb/sora-agent/issues/15).

</div>