# Provider Toggle

S0RA includes a unified provider system for **TTS**, **STT**, and **LLM Voice**.

## Provider Types

| Type | Providers | Use Case |
|------|-----------|----------|
| `llm_voice` | Gemini Live, Vapi | Full duplex conversation |
| `voice_platform` | Vapi, ElevenLabs | Managed conversation platforms |
| `tts` | Edge TTS, OpenAI TTS, ElevenLabs | Text → Speech |
| `stt` | Whisper | Speech → Text |

## CLI Management

```bash
# List all providers
sora voice providers list

# Enable/disable
sora voice providers enable gemini-live
sora voice providers disable vapi

# Configure (interactive)
sora voice providers config edge-tts

# Quick toggle in chat
# /providers enable elevenlabs
```

## Configuration

```yaml
voice:
  providers:
    gemini_live:  { enabled: true,  configured: true,  type: llm_voice, model: gemini-3.1-flash-live-preview }
    vapi:         { enabled: false, configured: false, type: voice_platform }
    elevenlabs:   { enabled: false, configured: false, type: tts }
    edge_tts:     { enabled: true,  configured: true,  type: tts }
    openai_tts:   { enabled: false, configured: false, type: tts }
    whisper:      { enabled: false, configured: false, type: stt }
```

## Runtime Switching

```python
# In chat, switch TTS provider
/tts edge-tts

# Switch STT
/stt whisper

# Switch LLM Voice
/voice gemini-live
```

## Web Dashboard

The dashboard's **Providers** panel shows:
- All providers with enable/disable toggles
- Configuration status
- Real-time provider health
- One-click switching
