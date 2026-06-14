# SIP Configuration

SIP registration is managed via Asterisk `pjsip.conf`, not dynamically via ARI.

## Configuration

```bash
# Shows SIP status
sora voice sip status

# Informational — registration via pjsip.conf
sora voice sip register --username sora --password pass --domain asterisk.local
sora voice sip unregister
```

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
