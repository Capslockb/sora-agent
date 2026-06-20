# Quick Start

This guide gets SORA installed and explains which commands are production-ready today versus migration scaffolding.

## 1. Install

```bash
# Recommended: isolated install
pipx install git+https://github.com/Capslockb/sora-agent

# Or development install
git clone https://github.com/Capslockb/sora-agent
cd sora-agent
uv pip install -e ".[dev]"
```

## 2. Run setup

```bash
sora setup
```

The interactive wizard/config paths cover:

1. model provider configuration;
2. Discord-related IDs and tokens;
3. Gemini Live / Vapi / ElevenLabs config values;
4. MCP configuration;
5. memory settings;
6. provider/tool toggles.

Config is stored under `~/.sora/` by default, or under `SORA_HOME` when that env var is set.

## 3. Check SORA state

```bash
sora status          # Overall system status
sora doctor          # Diagnostics
sora voice status    # Voice command status object
sora mcp status      # MCP status
```

## 4. Start the API backend

```bash
sora-api
```

Default bind falls back to:

```text
0.0.0.0:8080
```

Useful endpoints:

```text
/health
/api/status
/api/voice/status
/api/config
/api/config/env
/api/mcp/status
```

## 5. Voice commands: current truth

SORA has voice commands, but they are **not yet the production Discord/Gemini runtime**.

```bash
sora voice live --guild <GUILD_ID> --channel <CHANNEL_ID>
sora voice vapi --guild <GUILD_ID> --channel <CHANNEL_ID>
sora voice elevenlabs --guild <GUILD_ID> --channel <CHANNEL_ID>
sora voice status
sora voice leave --guild <GUILD_ID>
```

Current behavior:

- the commands validate required config/env values;
- they return status objects;
- they do not yet launch the full long-running Discord receive/playback + provider runtime;
- `sora voice status` currently reports no active bridge registry behind it.

Read: [`sora-bridge-status.md`](sora-bridge-status.md)

## 6. Working Gemini Live voice today

For live Discord + Gemini audio today, use the dedicated Gemini bridge repo:

```bash
git clone https://github.com/Capslockb/gemini-live-discord-bridge.git
cd gemini-live-discord-bridge
./install.sh
systemctl --user restart hermes-gateway
```

Then in Discord:

```text
/voice-live
```

Use SORA as the migration/control layer until the working Gemini bridge runtime is transplanted or wrapped.

## 7. MCP

```bash
sora mcp start
sora mcp status
sora mcp list
sora mcp catalog
sora mcp ws status
```

## 8. VOIP controls

```bash
sora voice sip status
sora voice ari status
sora voice voip-status
sora voice voip-config show
```

These are control/config surfaces for Asterisk/ARI/SIP/Dograh work. Confirm the underlying services are actually running before treating status output as a live call bridge.

## 9. TUI

```bash
cd ui-tui
npm install
npm run build
cd ..
sora tui
```

Depending on install layout, `sora tui` may require the TUI package to be built first.
