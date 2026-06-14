# sora voice

Voice bridge management for Discord and VOIP.

```bash
sora voice <SUBCOMMAND>
```

## Discord Bridges

| Command | Description |
|---------|-------------|
| `live` | Start Gemini Live bridge |
| `vapi` | Start Vapi bridge |
| `elevenlabs` | Start ElevenLabs bridge |
| `status` | Show bridge status |
| `leave` | Stop bridge |

## VOIP (Asterisk + Dograh)

| Command | Description |
|---------|-------------|
| `sip` | Manage SIP registration |
| `ari` | Manage ARI connection |
| `call` | Place outbound call |
| `hangup` | Hang up call(s) |
| `voip-status` | Full VOIP status |
| `voip-config` | Manage VOIP config |

## Providers

```bash
sora voice providers list
sora voice providers enable gemini-live
sora voice providers disable vapi
```