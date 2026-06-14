# VOIP Troubleshooting

## Common Issues

### ARI Not Connected

```bash
sora voice ari status
# {"connected": false, ...}
```

**Check:**
1. Asterisk running: `systemctl status asterisk`
2. ARI enabled: `asterisk -rx "module show like res_ari"`
3. `ari.conf` correct: user `sora`, correct password
4. Network: `curl http://asterisk:8088/ari/applications` returns JSON

### Dograh Connection Failed

```bash
sora voice voip-status
# "dograh": {"connected": false, ...}
```

**Check:**
1. Dograh running: `docker ps | grep dograh`
2. WS URL correct: `wss://dograh.local/ws` (or IP)
3. API key matches Dograh config
4. SSL cert valid (if using WSS)

### No Audio / One-Way Audio

**RTP Port Issues:**
```bash
# Check port range
sora voice voip-config show | grep rtp_port_range

# Verify firewall
sudo ufw allow 10000:20000/udp

# Check Asterisk RTP
asterisk -rx "rtp show summary"
```

**Codec Mismatch:**
- Asterisk: `disallow=all; allow=ulaw,alaw,opus`
- Dograh expects 48kHz PCM (SLIN48)
- Sora handles transcoding via RTP handler

### Call Drops Immediately

**Check:**
1. ARI app registered: `asterisk -rx "ari show apps"`
2. Dialplan routes to Stasis: `exten => s,1,Stasis(sora-bridge)`
3. Check Asterisk logs: `tail -f /var/log/asterisk/full`

### SIP Registration Failed

```bash
asterisk -rx "pjsip show registrations"
asterisk -rx "pjsip show endpoint sora-endpoint"
```

## Debug Mode

```bash
# Enable debug logging
export SORA_LOG_LEVEL=DEBUG
sora voice voip-status

# Asterisk CLI debug
asterisk -rvvv
> pjsip set logger on
> ari set debug on
```

## Log Locations

| Component | Log Path |
|-----------|----------|
| S0RA | `~/.sora/logs/sora.log` |
| Asterisk | `/var/log/asterisk/full` |
| Dograh | `docker logs dograh` |
| RTP | S0RA debug logs |
