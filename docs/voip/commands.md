# VOIP Call Commands

## Outbound Call

```bash
sora voice call "+155****4567" [--caller-id "Name"] [--auto-answer] [--record]
```

| Flag | Description |
|------|-------------|
| `--caller-id` | Caller ID to present (default: "Sora") |
| `--auto-answer` | Auto-answer when connected |
| `--record` | Record call to `~/.sora/recordings/` |

## Hangup

```bash
# Hangup specific channel
sora voice hangup --channel <CHANNEL_ID>

# Hangup all active calls
sora voice hangup --all
```

## Status

```bash
# Full VOIP status
sora voice voip-status

# SIP status
sora voice sip status

# ARI status
sora voice ari status
```

## Call Details (from voip-status)

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

## Recording

```yaml
voip:
  record_calls: true
  recording_dir: "~/.sora/recordings"
```

Recordings saved as WAV (48kHz, mono, mixed).
