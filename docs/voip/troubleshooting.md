# VOIP Troubleshooting

## Current runtime boundary

The checked-in VOIP startup paths are currently blocked before a usable bridge instance is constructed. Both `sora voip start` and the standalone VOIP entrypoint use stale configuration imports and do not match the current `VoipBridge` constructor. Track the lifecycle repair in [Issue #14](https://github.com/Capslockb/sora-agent/issues/14).

Until that issue is resolved and exact-head lifecycle tests pass:

- treat the commands below as configuration or external-service diagnostics, not proof that the S0RA VOIP bridge is running;
- expect `sora voice ari ...`, `sora voice call`, `sora voice hangup`, and `sora voice voip-status` to report that the bridge is not initialized;
- do not use live calls, recordings, or firewall changes as a substitute for repairing the local construction path;
- do not pass SIP, ARI, Dograh, or API credentials through ordinary command-line arguments. Secret handling remains tracked in [Issue #7](https://github.com/Capslockb/sora-agent/issues/7).

## Diagnose the local blocker first

If a S0RA VOIP command returns a bridge-initialization error, first confirm whether Issue #14 is still open. Installing or reconfiguring Asterisk and Dograh cannot repair the current local constructor mismatch.

The following command reads stored VOIP configuration without requiring a running bridge:

```bash
sora voice voip-config show
```

The implementation masks only the known top-level keys `asterisk_password` and `dograh_api_key`. Treat all other output as potentially sensitive and do not paste it into public issues or logs without review.

Do not use `sora voice voip-config set` for passwords, API keys, tokens, or other secrets. It accepts the value through process arguments and currently includes the supplied value in its response.

## External ARI checks

These checks can establish whether Asterisk and ARI are available independently of S0RA. They do not initialize the S0RA bridge.

```bash
systemctl status asterisk
asterisk -rx "module show like res_ari"
```

Review the configured ARI URL, application name, username, and network reachability without placing credentials in shell history. A direct ARI request may require authentication; avoid embedding credentials in a command that will be retained by the shell.

`sora voice ari status` is bridge-dependent. On the current startup path, an uninitialized-bridge response is expected and does not distinguish an Asterisk failure from the local lifecycle blocker.

## External Dograh checks

Confirm the Dograh process and its configured WebSocket endpoint independently:

```bash
docker ps --filter name=dograh
```

Check the configured URL scheme, hostname, certificate trust, and API-key source. Do not print the API key or place it in a URL. `sora voice voip-status` also requires an initialized S0RA bridge and is not currently an end-to-end connectivity test.

## Audio and RTP diagnostics

Audio troubleshooting is meaningful only after the bridge construction path is repaired and a call reaches the first external media attempt.

At that point, inspect:

1. the configured RTP port range on both Asterisk and S0RA;
2. NAT and firewall rules on the specific hosts and interfaces involved;
3. negotiated codecs and sample rates;
4. whether media is flowing in both directions;
5. bridge logs for capture, transcoding, forwarding, and shutdown events.

Do not copy a broad firewall-opening command from documentation into production. Restrict any UDP rule to the required hosts, interfaces, and port range after reviewing the deployment topology.

The repository contains RTP and transcoding components, but their presence is not evidence that the current entrypoints successfully wire them into a live call.

## Call drops and SIP registration

Asterisk-side checks such as the following remain useful after the local lifecycle issue is fixed:

```bash
asterisk -rx "ari show apps"
asterisk -rx "pjsip show registrations"
asterisk -rx "pjsip show endpoints"
```

Also verify that the dialplan routes calls to the intended Stasis application and inspect Asterisk logs for the exact call attempt.

The current `sora voice sip register` and `unregister` command surfaces are compatibility paths, not validated dynamic-registration workflows. Do not supply real SIP passwords through their `--password` arguments.

## Debug logging

```bash
export SORA_LOG_LEVEL=DEBUG
asterisk -rvvv
```

In the Asterisk console, protocol logging can expose numbers, headers, addresses, and authentication material. Enable it only for a bounded diagnostic window, store logs securely, redact them before sharing, and disable verbose logging afterward.

## Log locations

| Component | Typical location | Current caveat |
|---|---|---|
| S0RA | `~/.sora/logs/sora.log` | A usable VOIP session is not expected until Issue #14 is fixed. |
| Asterisk | `/var/log/asterisk/full` | May contain call metadata and sensitive protocol details. |
| Dograh | Container or service logs | Exact command depends on how Dograh is deployed. |
| RTP | S0RA/Asterisk debug logs | Media evidence is meaningful only after bridge construction succeeds. |

## Evidence required before calling VOIP operational

A repair should not be considered complete until the exact correction head demonstrates:

- both VOIP entrypoints import and construct the current bridge;
- foreground and detached modes preserve the intended configuration without secrets in process arguments;
- ARI, RTP, and Dograh clients are wired through one tested construction path;
- startup, first external attempt, status, shutdown, and negative paths are covered;
- documentation matches the tested behavior; and
- exact-head CI or equivalent reproducible validation evidence is attached.
