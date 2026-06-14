---
layout: home
hero:
  name: S0RA Agent
  text: Standalone Voice Agent CLI
  tagline: Built around Gemini Live, Vapi, ElevenLabs, and VOIP (Asterisk + Dograh). Mirrors Hermes architecture — works plug-n-play with Hermes or independently.
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
    details: Switch between Gemini Live, Vapi.ai, ElevenLabs, Edge TTS, OpenAI TTS, Whisper STT with a single CLI command.
  - icon: 📞
    title: VOIP / Asterisk + Dograh
    details: Connect your self-hosted PBX via Asterisk ARI. Route phone calls through Dograh to Gemini Live for AI conversations.
  - icon: 🔌
    title: MCP Integration
    details: Auto-detects running MCP servers (stdio + HTTP). WebSocket MCP with CLI management. Works with Honcho, OpenClaw, Hermes memory.
  - icon: 🎨
    title: Hermes DNA
    details: Same config system, profiles, skins, plugin architecture, constants, logging as Hermes. Drop-in familiar experience.
  - icon: 🌐
    title: Web Dashboard
    details: React + Vite dashboard with live voice demo, provider toggles, MCP status, and real-time system monitoring.
  - icon: 📦
    title: Install Anywhere
    details: pipx install git+https://github.com/Capslockb/sora-agent. Git-based updates. OpenWakeWord "Hey Sora" support.
  - icon: 🩺
    title: Doctor & Benchmark
    details: Built-in health checks, dependency verification, latency benchmarks, and configuration validation.
  - icon: 🤖
    title: ACP Server Mode
    details: Run as ACP server for editor integration (VS Code, Cursor, etc.) with full tool access.
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
sora setup           # Interactive wizard (Discord, Voice, MCP, VOIP, Memory, Providers)
sora voice live      # Start Gemini Live bridge (Discord)
sora voice vapi      # Start Vapi bridge (Discord)
sora voice providers # List/enable/disable TTS/STT/LLM providers
sora mcp start       # Start MCP server
sora voip-status     # Check VOIP bridge (Asterisk + Dograh)
sora doctor          # System health check
sora tui --build     # Launch Terminal UI
```

</div>