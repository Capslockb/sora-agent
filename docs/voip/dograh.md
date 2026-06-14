# Dograh / Gemini Live

Dograh is a self-hosted WebSocket proxy for Gemini Live API.

## Running Dograh

```bash
# Docker (recommended)
docker run -d   --name dograh   -p 8080:8080   -e GEMINI_API_KEY=***   -e MODEL=gemini-2.0-flash-exp   ghcr.io/your-org/dograh:latest

# Or from source
git clone https://github.com/your-org/dograh
cd dograh
docker compose up -d
```

## Configuration

```yaml
voip:
  dograh_ws_url: "wss://dograh.myhome.local/ws"
  dograh_api_key: "dograh-api-key"
  gemini_model: "gemini-2.0-flash-exp"
```

## Dograh Protocol

Dograh speaks the **Gemini Live protocol** with auth wrapper:

```json
// Session start
{
  "type": "sessionStart",
  "sessionId": "sora-call-abc123",
  "model": "gemini-2.0-flash-exp",
  "config": {
    "sampleRate": 48000,
    "channels": 1,
    "language": "en-US",
    "voice": "en-US-Neural2-F"
  },
  "metadata": {
    "call_id": "abc123",
    "caller": "+155****4567",
    "called": "+155****6543",
    "direction": "inbound"
  }
}

// Audio (base64 PCM)
{
  "type": "audio",
  "sessionId": "sora-call-abc123",
  "data": "base64-pcm-data"
}

// Transcript
{
  "type": "transcript",
  "sessionId": "sora-call-abc123",
  "transcript": "Hello, how can I help?"
}
```

## SSL/TLS

For production, use real certificates:

```bash
# Dograh behind nginx with Let's Encrypt
# nginx.conf
server {
    listen 443 ssl;
    server_name dograh.myhome.local;
    
    ssl_certificate /etc/letsencrypt/live/dograh.myhome.local/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dograh.myhome.local/privkey.pem;
    
    location /ws {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```
