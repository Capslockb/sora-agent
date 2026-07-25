# sora-voip Plugin

Asterisk ARI + Dograh/Gemini Live components for a phone-call AI bridge.

> **Current status: blocked.** The repository contains the ARI, RTP, Dograh, and bridge modules, but neither `sora voip start` nor the standalone `sora-voip` entrypoint can currently construct the checked-in `VoipBridge`. See [Issue #14](https://github.com/Capslockb/sora-agent/issues/14). Treat this page as a component and configuration reference, not proof of an operational end-to-end bridge.

## Implemented components

- **ARI Control** — Call origination, answering, hangup
- **RTP Media** — externalMedia/snoopChannel, port allocation
- **Dograh Bridge** — WebSocket to Dograh/Gemini Live
- **Call Recording** — WAV-format recording code
- **SIP Management** — Status and information only; registration remains in `pjsip.conf`

These components have not been validated through the currently broken startup lifecycle.

## Installation

The VOIP plugin is packaged as part of the root `sora-agent` project; `plugins/sora_voip` is not a separate installable Python project.

```bash
# From a cloned repository
pip install -e .

# After installing sora-agent
sora plugins enable sora-voip
```

Enabling the plugin does not repair the blocked VOIP entrypoints.

## Configuration

The intended configuration surface includes:

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

Store passwords and API keys in a protected configuration or environment source. Until Issue #7 is resolved, do not pass secrets through `sora voice voip-config set`: the value is accepted as an ordinary process argument and repeated in command output.

The two startup entrypoints currently use incomplete and inconsistent construction paths, so a populated configuration does not make the bridge runnable by itself.

## CLI commands

The following commands describe intended or bridge-dependent surfaces:

```bash
# SIP endpoint status; registration changes remain in pjsip.conf
sora voice sip status

# ARI diagnostics; these do not construct the missing bridge instance
sora voice ari connect
sora voice ari status
sora voice ari apps

# Calls; unavailable until a valid bridge lifecycle is restored
sora voice call "+155****4567" --caller-id "Sora" --auto-answer --record
sora voice hangup --all

# Status; requires an already running compatible bridge
sora voice voip-status

# Non-secret config values only
sora voice voip-config show
sora voice voip-config set dograh_ws_url "wss://..."
```

The current `sora voice sip register` and `sora voice sip unregister` commands do not create, remove, or reload Asterisk registrations. Do not supply real credentials to their `--password` arguments; the bridge does not use those values, while command-line arguments may be visible in shell history and process listings.

## Intended architecture

```text
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

The checked-in `VoipBridge` constructor requires explicit `AriClient`, `RtpHandler`, `DograhClient`, and configuration arguments. The current CLI entrypoints instead import a nonexistent `VoipConfig` and call `VoipBridge(config)`, which is why the architecture above is not reachable through the documented startup commands.

## Module structure

| Module | Purpose |
|--------|---------|
| `bridge.py` | Main orchestrator and call state machine |
| `ari_client.py` | ARI HTTP + WebSocket client |
| `rtp_handler.py` | RTP streams, port allocation, PCM↔RTP |
| `dograh_client.py` | Dograh WebSocket and session management |
| `__init__.py` | Plugin registration and lazy bridge access |
