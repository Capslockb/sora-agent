# sora setup

Interactive setup wizard for S0RA.

## Status

**PARTIAL**

The full wizard has runnable sections for model configuration, Discord, Gemini Live, Vapi, VOIP settings, MCP, memory, tools, and the optional wake word. Provider setup is not yet one complete or authoritative control surface:

- the voice-bridge section advertises seven backends but directly configures only Gemini Live and Vapi;
- declining the Gemini Live or Vapi enable prompt does not clear an existing `enabled: true` value;
- `sora setup --provider NAME` stores credential or identifier values but does not select or enable that provider in the runtime configuration;
- the ElevenLabs quick path currently uses `ELEVENLABS_AGENT_ID` for its first "API key" prompt and never collects `ELEVENLABS_API_KEY`.

These defects are tracked with the wider provider-state work in [Issue #15](https://github.com/Capslockb/sora-agent/issues/15).

## Usage

```bash
sora setup                    # Full interactive wizard
sora setup --provider NAME    # Credential-focused quick path
```

## Accepted quick-path names

```bash
sora setup --provider gemini-live
sora setup --provider vapi
sora setup --provider elevenlabs
sora setup --provider openai-realtime
sora setup --provider xai-grok
sora setup --provider ultravox
sora setup --provider retell
```

Treat these as credential-entry helpers, not proof that the provider has been selected, enabled, or reached successfully. Do not use the current ElevenLabs quick path for real setup; place `ELEVENLABS_API_KEY` and `ELEVENLABS_AGENT_ID` in `~/.sora/.env` through a protected editor or secret-management path until Issue #15 is resolved.

## What the full wizard currently does

1. Detects an existing OpenClaw configuration and offers a best-effort import.
2. Configures the main model provider and model.
3. Configures Discord bot credentials and identifiers.
4. Configures Gemini Live and Vapi bridge settings.
5. Optionally writes VOIP settings for Asterisk ARI and Dograh; this does not make the blocked VOIP lifecycle runnable.
6. Configures MCP discovery and server entries.
7. Configures memory settings.
8. Configures TTS, STT, web-search, and image-generation settings.
9. Optionally installs and configures OpenWakeWord.

## Verification boundary

```bash
sora status
sora providers list
sora voice providers list
```

These commands are diagnostic only. They read different configuration shapes and do not prove that quick setup selected the same provider or that an external voice runtime is healthy. Review `~/.sora/config.yaml` without exposing secrets, and verify the required variable names exist in `~/.sora/.env` without printing their values.

## Notes

- The wizard writes secrets to `~/.sora/.env` and non-secret settings to `~/.sora/config.yaml`.
- It does not start a voice bridge; live Discord audio still requires the external Hermes `discord-voice` runtime.
- Setup does not repair the provider-state divergence documented in Issue #15.
- OpenClaw import is best-effort and can overwrite the destination `.env`; back up existing S0RA configuration before accepting migration.