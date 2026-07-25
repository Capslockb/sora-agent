# VOIP Call Commands

> **Runtime status — startup blocked:** The command surfaces below exist, but they require a successfully initialized `sora-voip` bridge instance. The checked-in `sora voip start` command and installed standalone `sora-voip` entrypoint cannot currently construct that runtime. The standalone implementation still contains stale `sora-voip-bridge` help examples, but that console script is not exposed by `pyproject.toml`. See [Issue #14](https://github.com/Capslockb/sora-agent/issues/14).

Do not treat successful argument parsing or displayed command help as proof that call placement, media bridging, or lifecycle handling works on the current `main` head.

## Outbound call surface

```bash
sora voice call "+155****4567" [--caller-id "Name"] [--auto-answer] [--record]
```

| Flag | Description |
|------|-------------|
| `--caller-id` | Caller ID to request (default behavior is determined by the bridge/PBX configuration) |
| `--auto-answer` | Request auto-answer when connected |
| `--record` | Request call recording using the configured recording directory |

The command returns `VOIP bridge not initialized` when no bridge instance is available. It is not a workaround for the startup defect in Issue #14.

## Hangup surfaces

```bash
# Hang up a specific channel
sora voice hangup --channel <CHANNEL_ID>

# Hang up all active calls
sora voice hangup --all
```

These commands also require an initialized bridge and active ARI call state.

## Status surfaces

```bash
# Full VOIP status surface
sora voice voip-status

# SIP status surface
sora voice sip status

# ARI status surface
sora voice ari status
```

A status response only describes the available in-process bridge state. It does not validate construction of the documented startup entrypoints, PBX reachability, RTP flow, Dograh media exchange, or end-to-end call lifecycle.

## Illustrative call details

A detailed status response is intended to expose call information resembling the following schema after the bridge is repaired and running:

```json
{
  "active_calls": 1,
  "calls": [
    {
      "call_id": "abc123",
      "channel_id": "PJSIP/...-00001",
      "caller": "+155****4567",
      "called": "+155****6543",
      "direction": "inbound",
      "state": "bridged",
      "duration": 45,
      "recording": "/home/user/.sora/recordings/abc123_...wav",
      "dograh_session": "sora-call-abc123"
    }
  ]
}
```

This example is illustrative documentation, not exact-head runtime evidence.

## Recording configuration

```yaml
voip:
  record_calls: true
  recording_dir: "~/.sora/recordings"
```

The intended output is a mixed mono WAV stream at the configured sample rate. Recording behavior must be validated with the repaired bridge and exact-head lifecycle/media tests before it is treated as release-ready.
