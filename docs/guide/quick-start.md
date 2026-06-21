# Quick Start

## Status

**WORKING** for install, setup, status, and provider management.  
**PARTIAL** for starting live voice bridges (requires Hermes `discord-voice`).

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

All four should return clean output. If `sora doctor` reports missing env vars, that is expected until you complete setup.

## 3. Run setup wizard

```bash
sora setup
```

The interactive wizard guides you through model provider, Discord bot, voice bridges, VOIP, MCP, memory, providers, tools, and optional wake word.

Or quick-setup a specific voice provider:

```bash
sora setup --provider gemini-live      # Gemini API key
sora setup --provider vapi             # Vapi API key
sora setup --provider elevenlabs       # ElevenLabs API key + Agent ID
sora setup --provider openai-realtime  # OpenAI API key
sora setup --provider xai-grok         # xAI API key
sora setup --provider ultravox         # Ultravox API key
sora setup --provider retell           # Retell API key + Agent ID
```

## 4. Check provider state

```bash
sora voice providers list
sora voice providers enable gemini-live
sora voice providers enable edge-tts
```

## 5. Start live voice bridge (Discord)

**PARTIAL** — S0RA prepares the bridge arguments, but the live audio runtime is in the Hermes `discord-voice` plugin.

```bash
# Requires GEMINI_API_KEY + DISCORD_BOT_TOKEN
sora voice live --guild <GUILD_ID> --channel <CHANNEL_ID>
```

Make sure Hermes `discord-voice` is installed and enabled.

## 6. Check status

```bash
sora status          # Overall system status
sora voice status    # Voice bridges
sora mcp status      # MCP servers
```

## 7. Launch web dashboard

```bash
sora dashboard start --port 8080
# Open http://localhost:8080/health
```

Default port is `8080` (configurable with `SORA_API_PORT`).

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

## Pitfalls

- **No audio?** Check that Hermes `discord-voice` is installed, not just S0RA.
- **Provider unavailable?** Add the matching API key via `sora setup --provider <name>`.
- **TUI is a stub.** Do not demo it as a finished product.
- **Dashboard port mismatch.** Default is `8080`; some older docs may mention `3000`.

## Next steps

- Read [`architecture.md`](architecture.md) for the runtime map.
- Read [`bridge-elements.md`](../bridge-elements.md) for the operator tool surface.
- Read [`env-vars.md`](../env-vars.md) for all environment variables.
