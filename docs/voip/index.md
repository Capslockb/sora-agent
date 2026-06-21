# VOIP Integration

S0RA can integrate with an Asterisk PBX to bridge phone calls to voice AI providers via Dograh.

## Status

**PARTIAL** — plugin and CLI commands exist, but a live PBX is required.

## What is supported

- Asterisk ARI connection configuration.
- SIP endpoint registration state display.
- Outbound call placement via `sora voice call`.
- Dograh WebSocket gateway for Gemini Live audio.

## What is required externally

- An Asterisk PBX with ARI enabled.
- SIP/RTP network path between Asterisk and S0RA host.
- Dograh gateway with a valid API key.

## Environment variables

```bash
SORA_ARI_URL=http://asterisk.local:8088/ari
SORA_ARI_USER=sora
SORA_ARI_PASSWORD=***
SORA_DOGRAH_WS_URL=ws://dograh.local:8080/ws
SORA_DOGRAH_API_KEY=***
```

## Commands

```bash
sora voice sip          # Manage SIP registration
sora voice ari          # Manage ARI connection
sora voice call         # Place outbound call
sora voice hangup       # Hang up active calls
sora voice voip-status  # Show VOIP bridge status
sora voice voip-config  # Manage VOIP configuration
```

## Verification

```bash
sora voice voip-status
sora status --json
```

## See also

- [`asterisk.md`](asterisk.md) — Asterisk setup.
- [`dograh.md`](dograh.md) — Dograh/Gemini Live gateway.
- [`sip.md`](sip.md) — SIP configuration.
- [`ari.md`](ari.md) — ARI configuration.
- [`troubleshooting.md`](troubleshooting.md) — Common VOIP issues.
