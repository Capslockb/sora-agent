# ARI Configuration

ARI (Asterisk REST Interface) is the intended control channel for VOIP call management.

> **Runtime status — startup blocked:** The ARI command surfaces require an initialized `sora-voip` bridge. The checked-in `sora voip start` command and installed standalone `sora-voip` entrypoint cannot currently construct that runtime. The standalone implementation still contains stale `sora-voip-bridge` help examples, but that console script is not exposed by `pyproject.toml`. See [Issue #14](https://github.com/Capslockb/sora-agent/issues/14).

## Connection management surfaces

```bash
# Request connection for an already initialized bridge
sora voice ari connect --app sora-bridge

# Inspect in-process ARI status
sora voice ari status

# Request the registered application list
sora voice ari apps
```

These commands do not create the missing bridge instance. When the plugin is not initialized they return an error rather than establishing an independent ARI connection. Do not use them as startup or release verification while Issue #14 remains open.

## App registration

The intended bridge registers the `sora-bridge` Stasis application after a repaired runtime starts successfully. Configure the ARI user in `ari.conf`:

```ini
[general]
enabled = yes

[sora]
type = user
read_only = no
password = secure-password
```

Protect the ARI credential and do not place it in ordinary command-line arguments, issue reports, logs, or committed example files.

## Intended event flow

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

This is the designed flow, not exact-head evidence that the current entrypoints complete it.

## Outbound call surface

```bash
sora voice call "+155****4567" --caller-id "Sora" --auto-answer --record
```

After the runtime construction path is repaired, the intended flow is:

1. ARI originates a channel to `PJSIP/+155****4567`.
2. The channel enters the `sora-bridge` Stasis application with outbound call arguments.
3. The bridge follows the same media and cleanup path as an inbound call.

Outbound origination and media flow remain unverified on the current `main` head and require exact-head lifecycle and integration validation.
