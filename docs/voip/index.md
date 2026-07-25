# VOIP Integration

S0RA can integrate with an Asterisk PBX to bridge phone calls to voice AI providers via Dograh.

## Status

**PARTIAL — startup currently blocked.** Configuration, status, and management command surfaces exist, but the checked-in `sora voip start` command and installed standalone `sora-voip` entrypoint do not currently construct the bridge runtime successfully. Both import a `VoipConfig` symbol that is not defined in `plugins/sora_voip/bridge.py`, and both call `VoipBridge` with a single configuration object even though the current constructor requires an `AriClient`, `RtpHandler`, `DograhClient`, and configuration mapping. The standalone implementation also contains stale `sora-voip-bridge` help examples even though that console script is not exposed by `pyproject.toml`. See [Issue #14](https://github.com/Capslockb/sora-agent/issues/14).

A live PBX and valid credentials are still required after the local lifecycle blocker is repaired, but they do not resolve the current construction mismatch.

## What is supported

- Asterisk ARI connection configuration.
- SIP endpoint registration state display.
- VOIP configuration and status command surfaces.
- Dograh WebSocket configuration for Gemini Live audio.

## What is not currently verified

- Starting the full bridge through `sora voip start`.
- Starting the installed standalone `sora-voip` entrypoint.
- End-to-end outbound call placement and media bridging from the current `main` head.
- Detached startup preserving the complete resolved runtime configuration without exposing secrets through command-line arguments.

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

Store secrets in protected environment or configuration sources. Do not place real credentials in ordinary command-line arguments.

## Commands

The following commands expose management or configuration surfaces. They are not proof that the full VOIP bridge startup path is currently runnable.

```bash
sora voice sip          # Manage SIP registration state/information
sora voice ari          # Manage ARI connection state/information
sora voice call         # Outbound-call command surface
sora voice hangup       # Hang-up command surface
sora voice voip-status  # Show VOIP bridge status
sora voice voip-config  # Manage VOIP configuration
```

Do not use `sora voip start` or `sora-voip` as release verification until Issue #14 is resolved and exact-head lifecycle tests pass.

## Verification

```bash
sora voice voip-status
sora status --json
```

These commands verify only the available status surfaces. They do not validate bridge construction, PBX connectivity, RTP media, or call lifecycle.

## See also

- [`asterisk.md`](asterisk.md) — Asterisk setup.
- [`dograh.md`](dograh.md) — Dograh/Gemini Live gateway.
- [`sip.md`](sip.md) — SIP configuration.
- [`ari.md`](ari.md) — ARI configuration.
- [`troubleshooting.md`](troubleshooting.md) — Common VOIP issues.
