# SIP Configuration

SIP registration is managed via Asterisk `pjsip.conf`, not dynamically via ARI.

## CLI Boundary

```bash
# Queries the initialized VOIP bridge for Asterisk endpoint status
sora voice sip status
```

The current `sora voice sip register` and `sora voice sip unregister` commands are informational compatibility paths. They do not create, remove, or reload Asterisk registrations, and credentials supplied through `--password` are not used by the bridge.

Do not pass real SIP credentials through those command-line arguments. Ordinary process arguments may be visible in shell history and process listings. Configure registrations in `pjsip.conf` and use the status command or the Asterisk CLI to verify them. Runtime removal of the unused credential arguments is tracked in Issue #7.

## pjsip.conf Registration

```ini
; Static registration to provider
[provider-registration]
type = registration
transport = transport-udp
outbound_auth = provider-auth
server_uri = sip:sip.provider.com
client_uri = sip:sora@your-domain.com
retry_interval = 30
expiration = 3600
contact_user = sora

[provider-auth]
type = auth
auth_type = userpass
username = sip-username
password = sip-password
```

## Verify Registration

```bash
asterisk -rx "pjsip show registrations"
# Should show: provider-registration  Registered
```
