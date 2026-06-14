# Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        S0RA Agent CLI                           │
├─────────────────────────────────────────────────────────────────┤
│  Constants  │  Config  │  Logging  │  Profiles  │  Skins  │     │
├─────────────────────────────────────────────────────────────────┤
│                    Plugin Manager                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ sora-hermes  │  │  sora-voip   │  │      built-in        │  │
│  │  (Discord)   │  │ (Asterisk)   │  │  (MCP, Memory, etc)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  Voice Layer  │  MCP Layer  │  Memory Layer  │  Tool Layer    │
└─────────────────────────────────────────────────────────────────┘
```

## Core Modules

| Module | Path | Purpose |
|--------|------|---------|
| Constants | `sora_constants/` | Paths, defaults, version |
| Config | `sora_cli/config.py` | YAML + env merge, profiles |
| Logging | `sora_logging/` | Structured, colored, file+stdout |
| Profiles | `sora_cli/profile.py` | Isolated config directories |
| Skins | `sora_cli/skin.py` | Theme engine (YAML + built-in) |
| Plugins | `sora_cli/plugins.py` | Discovery, enable/disable, YAML |

## Voice Architecture

### Discord Voice Bridges

```
Discord Gateway (Voice WS)
       │
       ▼
┌──────────────────┐
│  sora-hermes     │  Plugin
│  bridge.py       │  → VoiceLiveBridge
│  LiveAudioSource │  → Discord AudioSource
│  VoiceListener   │  → Opus → PCM → Gemini
└──────────────────┘
       │
       ▼
Gemini Live API (WSS)
```

### VOIP Bridge (Asterisk + Dograh)

```
Asterisk (SIP/RTP)          Dograh/Gemini Live
       │                          │
       ▼                          ▼
┌──────────────────────────────────────────┐
│         sora-voip Plugin                 │
│  ┌──────────┐  ┌─────────┐  ┌──────────┐ │
│  │ ARI      │  │  RTP    │  │ Dograh   │ │
│  │ Client   │◄─┤ Handler │──►│ Client   │ │
│  └──────────┘  └─────────┘  └──────────┘ │
└──────────────────────────────────────────┘
```

## MCP Layer

- **Auto-discovery**: Scans ports 3000-3010 + stdio processes
- **WebSocket MCP**: Native WS server on port 3000 (configurable)
- **CLI Management**: `sora mcp start/status/stop/catalog`

## Plugin System

```python
# plugin.yaml
name: my-plugin
version: 1.0.0
description: My plugin
entry_point: my_plugin

# my_plugin/__init__.py
def register(ctx):
    ctx.register_tool(my_tool)
    ctx.register_slash_command(my_command)
```
