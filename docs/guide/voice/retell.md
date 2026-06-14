# Retell AI (Telephony + Web Calls)

## Overview

Retell AI provides a **voice agent platform** for telephony and web calls. Uses REST API to create calls and WebSocket for real-time audio transport.

## Requirements

| Requirement | Details |
|-------------|---------|
| `RETELL_API_KEY` | Retell API key from app.retellai.com |
| `RETELL_AGENT_ID` | Pre-created Retell agent ID |

## Configuration

```bash
sora setup --provider retell
# Prompts: RETELL_API_KEY → RETELL_AGENT_ID → voice ID
```

Or manually in `~/.sora/config.yaml`:

```yaml
voice:
  retell:
    enabled: false
    agent_id: ""
    voice_id: ""
```

## Start Bridge

```bash
sora voice retell
sora voice retell --guild 123... --channel 456...
sora voice retell --guild 123... --user 987...
```

## Flow

```
Create web call → Get access token → WebSocket connect → Bidirectional PCM audio
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "RETELL_API_KEY not set" | `export RETELL_API_KEY=...` or `sora setup --provider retell` |
| "RETELL_AGENT_ID not set" | Create an agent at app.retellai.com → copy ID → `export RETELL_AGENT_ID=...` |
| Call fails | Verify agent ID and voice ID exist in Retell dashboard |
