# sora-voip Plugin

Asterisk ARI + Dograh/Gemini Live for phone call AI.

## Features

- **ARI Control** — Call origination, answering, hangup
- **RTP Media** — externalMedia/snoopChannel, port allocation
- **Dograh Bridge** — WebSocket to Dograh/Gemini Live
- **Call Recording** — WAV format, mixed audio
- **SIP Management** — Status, info (config via pjsip.conf)

## Installation

```bash
# Built into S0RA repo
pip install -e ./plugins/sora_voip
# Or after pipx install:
sora plugins enable sora-voip
```

## Configuration

```yaml
voip:
  asterisk_ari_url: "http://asterisk:8088/ari"
  asterisk_username: "sora"
  asterisk_password: "secure-password"
  asterisk_app_name: "sora-bridge"
  dograh_ws_url: "wss://dograh.myhome.local/ws"
  dograh_api_key: "dograh-api-key"
  gemini_model: "gemini-2.0-flash-exp"
  sample_rate: 48000
  rtp_port_range: "10000-20000"
  auto_answer: true
  record_calls: false
  recording_dir: "~/.sora/recordings"
```

## CLI Commands

```bash
# SIP
sora voice sip status

# ARI
sora voice ari connect
sora voice ari status
sora voice ari apps

# Calls
sora voice call "+155****4567" --caller-id "Sora" --auto-answer --record
sora voice hangup --all

# Status
sora voice voip-status

# Config
sora voice voip-config show
sora voice voip-config set dograh_ws_url "wss://..."
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    VoipBridge                       │
├─────────────┬─────────────┬─────────────────────────┤
│  AriClient  │  RtpHandler │    DograhClient         │
│  (HTTP+WS)  │  (UDP/RTP)  │    (WSS)                │
└─────────────┴─────────────┴─────────────────────────┘
       │              │                   │
       ▼              ▼                   ▼
  Asterisk      RTP Ports            Dograh/Gemini
  (ARI/WS)     (10000-20000)         (WSS)
```

## Module Structure

| Module | Purpose |
|--------|---------|
| `bridge.py` | Main orchestrator, call state machine |
| `ari_client.py` | ARI HTTP + WebSocket client |
| `rtp_handler.py` | RTP streams, port allocation, PCM↔RTP |
| `dograh_client.py` | Dograh WebSocket, session management |
| `__init__.py` | Plugin registration, lazy bridge init |
