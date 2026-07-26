# Quick Start

## Status

**WORKING** for installation and the basic CLI entry points.  
**PARTIAL** for setup and provider management: the setup wizard, both provider command families, and the dashboard/API do not share one complete provider-state contract; see [Issue #15](https://github.com/Capslockb/sora-agent/issues/15).  
**PARTIAL** for starting live voice bridges because live Discord audio requires Hermes `discord-voice`.  
**PARTIAL** for the dashboard control API because authentication and safe network defaults remain open under [Issue #13](https://github.com/Capslockb/sora-agent/issues/13).

## 1. Install

```bash
# Recommended: pipx (isolated, auto-updatable)
pipx install git+https://github.com/Capslockb/sora-agent

# Or development install
git clone https://github.com/Capslockb/sora-agent
cd sora-agent
pip install -e .
```

## 2. Verify the CLI

```bash
sora --version
sora --help
sora doctor
sora status
```

All four should return output. Missing credentials and external services can still produce warnings or partial status after installation.

## 3. Run the setup wizard

```bash
sora setup
```

The interactive wizard covers the main model, Discord, Gemini Live, Vapi, VOIP settings, MCP, memory, tools, and optional wake word. Its voice section advertises seven backends but directly configures only Gemini Live and Vapi. Declining their enable prompts also does not clear an existing enabled value.

Credential-focused quick paths accept these names:

```bash
sora setup --provider gemini-live
sora setup --provider vapi
sora setup --provider elevenlabs
sora setup --provider openai-realtime
sora setup --provider xai-grok
sora setup --provider ultravox
sora setup --provider retell
```

A successful quick path stores credential or identifier values only; it does not prove that the provider was selected or enabled in the runtime configuration. The current ElevenLabs path is additionally unsafe for configuration accuracy because its first prompt writes to `ELEVENLABS_AGENT_ID` and never collects `ELEVENLABS_API_KEY`. Configure those two variables through a protected edit of `~/.sora/.env` until Issue #15 is resolved.

## 4. Inspect provider state

```bash
sora providers list
sora voice providers list
```

These are diagnostic views over different configuration shapes. Do not treat either result as authoritative runtime selection, and do not use a successful setup command as proof that an external provider is reachable.

## 5. Start live voice bridge (Discord)

**PARTIAL** — S0RA prepares bridge arguments, but the live audio runtime is in the Hermes `discord-voice` plugin.

```bash
# Requires GEMINI_API_KEY + DISCORD_BOT_TOKEN
sora voice live --guild <GUILD_ID> --channel <CHANNEL_ID>
```

Make sure Hermes `discord-voice` is installed and enabled.

## 6. Check status

```bash
sora status          # Configuration and local dependency snapshot
sora voice status    # S0RA voice state view
sora mcp status      # MCP server state view
```

Status output is diagnostic. It does not perform complete provider reachability checks or reconcile the provider schemas tracked in Issue #15.

## 7. Launch web dashboard

```bash
sora dashboard start --host 127.0.0.1 --port 3000 --api-port 8080
# UI preview: http://127.0.0.1:3000
# API health: http://127.0.0.1:8080/health
```

`--port` controls the UI preview port and `--api-port` controls the FastAPI control API; the ports must be different. `--host` currently applies only to the API server. The UI is launched separately through `npx serve`, and the CLI does not forward an explicit UI bind host.

Use `dashboard start` only on a trusted local machine until Issue #13 is resolved. The control API has sensitive read and mutation routes without authentication; do not run the current dashboard on a shared or network-exposed host, and do not publish either listener through a LAN, tunnel, container port, reverse proxy, or the public internet.

## 8. Launch TUI

```bash
sora tui
```

**PLANNED** — currently falls back to a chat REPL.

## Verification commands

```bash
sora --help
sora status --json
sora voice status
sora mcp status
python -m pytest tests/ -q
```

These are manual verification steps until the staged pytest workflow is activated; see [Issue #12](https://github.com/Capslockb/sora-agent/issues/12).

## Pitfalls

- **Setup is not a seven-provider selector.** The full voice wizard configures Gemini Live and Vapi directly; quick paths mainly store credentials.
- **ElevenLabs quick setup is miswired.** Do not paste an API key into its current first prompt; configure `ELEVENLABS_API_KEY` and `ELEVENLABS_AGENT_ID` separately.
- **Provider views disagree.** `sora providers`, `sora voice providers`, setup, and the dashboard/API do not share one canonical provider state.
- **No audio?** Check that Hermes `discord-voice` is installed, not just S0RA.
- **TUI is a stub.** Do not demo it as a finished product.
- **Dashboard command flags.** `dashboard start` accepts `--host`, `--port`, and `--api-port`. `--port` is the UI preview port; `--api-port` is the control API port.
- **Dashboard bind scope.** `--host` constrains the API server only. The current command does not expose an explicit UI bind-host option, so treat the whole dashboard as local-development-only.

## Next steps

- Read [`architecture.md`](architecture.md) for the runtime map.
- Read [`bridge-elements.md`](../bridge-elements.md) for the operator tool surface.
- Read [`env-vars.md`](../env-vars.md) for all environment variables.