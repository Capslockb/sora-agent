# ARI Configuration

ARI (Asterisk REST Interface) is the control channel for call management.

## Connection

```bash
# Connect ARI app
sora voice ari connect --app sora-bridge

# Check status
sora voice ari status

# List registered apps
sora voice ari apps
```

## App Registration

The `sora-bridge` app is registered when the bridge starts. In `ari.conf`:

```ini
[general]
enabled = yes

[sora]
type = user
read_only = no
password = secure-password
```

## Event Flow

```
Inbound Call
    │
    ▼
StasisStart (channel enters app)
    │
    ▼
ARI: answer channel
    │
    ▼
ARI: externalMedia (RTP to Sora)
    │
    ▼
Dograh sessionStart
    │
    ▼
Conversation (RTP ↔ Dograh)
    │
    ▼
Hangup / StasisEnd
    │
    ▼
Cleanup (RTP stop, Dograh sessionEnd)
```

## Outbound Calls

```bash
sora voice call "+155****4567" --caller-id "Sora" --auto-answer --record
```

Flow:
1. ARI `originate` to `PJSIP/+155****4567`
2. Channel enters `sora-bridge` app (with `outbound,callId` args)
3. Same flow as inbound
