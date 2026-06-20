---
layout: home
hero:
  name: S0RA Agent
  text: SORA Bridge Control Layer
  tagline: CLI, profiles, FastAPI backend, MCP, Hermes plugin, VOIP controls, and the future home for SORA-owned voice bridge runtime.
  image:
    src: /sora-agent/favicon.svg
    alt: S0RA Agent
  actions:
    - theme: brand
      text: Quick Start
      link: /guide/quick-start
    - theme: alt
      text: Bridge Status
      link: /guide/sora-bridge-status
    - theme: alt
      text: GitHub Repo
      link: https://github.com/Capslockb/sora-agent

features:
  - icon: 🎛️
    title: Control Layer First
    details: SORA currently provides CLI, config, profiles, status, API, MCP, Hermes tooling, and migration scaffolding for voice providers.
  - icon: 🎙️
    title: Voice Runtime Migration
    details: Gemini/Vapi/ElevenLabs command paths exist, but the production Discord/Gemini live runtime still lives in gemini-live-discord-bridge until transplanted or wrapped.
  - icon: 🔌
    title: MCP Integration
    details: MCP command and API surfaces exist for status, detection, stdio/HTTP-style configuration, and WebSocket MCP controls.
  - icon: 📞
    title: VOIP / Asterisk + Dograh
    details: SIP, ARI, call, hangup, voip-status, and voip-config command surfaces are present for self-hosted telephony work.
  - icon: 🧩
    title: Hermes Plugin
    details: ships a sora-hermes plugin with SORA voice and MCP tools; slash commands currently guide users to the dedicated voice plugins.
  - icon: 🖥️
    title: API + TUI Surfaces
    details: FastAPI backend and Ink/React TUI source are present; runtime-backed voice process management is still being built out.
  - icon: 🩺
    title: Doctor & Status
    details: Built-in setup, status, doctor, benchmark, config, logs, plugin, skills, and cron command paths.
---

<div class="vp-doc" style="text-align: center; margin-top: 2rem;">

## Start Here

```bash
# Install
pipx install git+https://github.com/Capslockb/sora-agent

# Configure and inspect SORA
sora setup
sora status
sora doctor

# Run the API backend
sora-api
```

## Important Voice Note

For **working live Gemini voice in Discord today**, use `Capslockb/gemini-live-discord-bridge` and its `/voice-live` command.

In this repo, `sora voice live` is currently a SORA control/scaffold path: it validates config and returns a start-status response, but the full Discord/Gemini runtime has not yet been transplanted.

Read the status guide before relying on voice runtime behavior:

[Bridge status →](/guide/sora-bridge-status)

</div>
