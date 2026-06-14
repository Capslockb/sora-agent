# VOIP Setup

Connect your self-hosted Asterisk PBX + Dograh to S0RA for AI phone calls.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Phone      │────►│  Asterisk   │────►│  Dograh     │
│  (SIP/RTP)  │     │  (ARI)      │     │  (Gemini)   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────────────────────┐
                    │      S0RA VOIP Bridge       │
                    │  (sora-voip plugin)         │
                    └─────────────────────────────┘
```

## Prerequisites

| Component | Version | Config |
|-----------|---------|--------|
| Asterisk | 18+ | `ari.conf`, `pjsip.conf` |
| Dograh | Self-hosted | `wss://dograh.local/ws` |
| S0RA | 0.1+ | `sora-voip` plugin |

## Quick Setup

```bash
# 1. Enable plugin
sora plugins enable sora-voip

# 2. Configure via wizard
sora setup
# Section 3b: VOIP Integration

# 3. Or manually edit config
```

## Configuration

```yaml
# ~/.sora/config.yaml
voip:
  asterisk_ari_url: "http://asterisk:8088/ari"
  asterisk_username: "sora"
  asterisk_password: "secure-password"
  asterisk_app_name: "sora-bridge"
  dograh_ws_url: "wss://dograh.myhome.local/ws"
  dograh_api_key: "your-dograh-api-key"
  gemini_model: "gemini-2.0-flash-exp"
  sample_rate: 48000
  rtp_port_range: "10000-20000"
  auto_answer: true
  record_calls: false
  recording_dir: "~/.sora/recordings"
```

## Verification

```bash
# Check status
sora voice voip-status

# Test ARI connection
sora voice ari connect
sora voice ari status

# Test SIP (info only — configure in pjsip.conf)
sora voice sip status
```
