# VOIP Setup

> **Runtime status — startup blocked:** This page documents the intended topology and configuration preparation. The checked-in `sora voip start` and standalone `sora-voip-bridge` entrypoints cannot currently construct the bridge runtime. A live PBX and valid credentials do not bypass that local lifecycle defect. See [Issue #14](https://github.com/Capslockb/sora-agent/issues/14).

Prepare a self-hosted Asterisk PBX and Dograh configuration for S0RA voice calls after the runtime construction path is repaired and validated.

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

These prerequisites describe the intended deployment. They are not proof that the current bridge entrypoints start successfully.

## Configuration preparation

```bash
# 1. Enable the plugin configuration surface
sora plugins enable sora-voip

# 2. Configure via the setup wizard
sora setup
# Section 3b: VOIP Integration

# 3. Or manually edit the VOIP configuration
```

Enabling or configuring the plugin does not resolve the entrypoint construction blocker in Issue #14.

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

Protect configuration files containing PBX or Dograh credentials. Do not commit real secrets or pass them through ordinary command-line arguments.

## Diagnostic surfaces

```bash
# Inspect the bridge status surface
sora voice voip-status

# Inspect ARI and SIP status surfaces
sora voice ari status
sora voice sip status
```

These commands require a successfully initialized bridge instance. On the current documented startup paths they may report that the VOIP bridge is not initialized. They do not validate bridge construction, PBX connectivity, RTP media, or end-to-end call lifecycle.

`sudo voice ari connect` is not a startup workaround: the command also depends on an existing bridge instance. Do not use these status or management commands as release evidence until Issue #14 is resolved and exact-head lifecycle tests pass.
