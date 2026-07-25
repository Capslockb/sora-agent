# sora voice

Voice bridge management for Discord and VOIP.

```bash
sora voice <SUBCOMMAND>
```

## Discord Bridges

| Command | Description |
|---------|-------------|
| `live` | Validate and prepare Gemini Live bridge inputs |
| `vapi` | Validate and prepare Vapi bridge inputs |
| `elevenlabs` | Validate and prepare ElevenLabs bridge inputs |
| `status` | Show S0RA voice state |
| `leave` | Request bridge stop behavior |

The live Discord runtime is provided by the separate Hermes `discord-voice` plugin; these commands do not make this repository a standalone Discord voice bridge.

## VOIP (Asterisk + Dograh)

| Command | Description |
|---------|-------------|
| `sip` | SIP management surface |
| `ari` | ARI management surface |
| `call` | Outbound-call surface |
| `hangup` | Hang-up surface |
| `voip-status` | VOIP status surface |
| `voip-config` | VOIP configuration surface |

The current VOIP bridge startup lifecycle is blocked under [Issue #14](https://github.com/Capslockb/sora-agent/issues/14). These command names do not prove that a bridge is initialized or that call/media operations are available.

## Providers

```bash
sora voice providers list
sora voice providers enable gemini-live
sora voice providers disable vapi
sora voice providers config edge-tts
```

**Experimental:** `sora voice providers` is not an alias of the top-level `sora providers` command. It uses a separate `voice.providers` mapping, has a smaller default registry, and its `config` action is a placeholder that redirects to `sora setup`. Changes made here may not be reflected by top-level provider status or runtime selection.

Use `sora setup` for initial configuration and read the [provider-management guide](../../guide/voice/providers.md) before relying on either command family. Canonical state and migration work is tracked in [Issue #15](https://github.com/Capslockb/sora-agent/issues/15).
