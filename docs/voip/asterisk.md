# Asterisk Configuration

## ari.conf

```ini
[general]
enabled = yes
pretty = yes
allowed_origins = *

[sora]
type = user
read_only = no
password = secure-password
```

Restart Asterisk: `asterisk -rx "module reload res_ari.so"`

## pjsip.conf (SIP Endpoint)

```ini
[transport-udp]
type = transport
protocol = udp
bind = 0.0.0.0:5060

[sora-endpoint]
type = endpoint
transport = transport-udp
context = from-sora
disallow = all
allow = ulaw,alaw,opus
auth = sora-auth
aors = sora-aor
direct_media = no
rtp_symmetric = yes
force_rport = yes
rewrite_contact = yes

[sora-auth]
type = auth
auth_type = userpass
username = sora
password = secure-password

[sora-aor]
type = aor
max_contacts = 1
remove_existing = yes
```

## extensions.conf (Dialplan)

```ini
[from-sora]
exten => s,1,NoOp(Inbound to Sora)
 same => n,Stasis(sora-bridge)
 same => n,Hangup()

; Outbound via Sora
[sora-outbound]
exten => _X.,1,NoOp(Outbound via Sora)
 same => n,Dial(PJSIP/${EXTEN}@your-provider,30)
 same => n,Hangup()
```

## Verify ARI

```bash
# Check ARI is running
asterisk -rx "ari show apps"
# Should show: sora-bridge

# Check endpoint
asterisk -rx "pjsip show endpoints"
# Should show: sora-endpoint
```
