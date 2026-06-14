# Provider Toggle

S0RA includes a unified provider system for **TTS**, **STT**, and **LLM Voice**.

## Provider Types

| Type | Providers | Use Case |
|------|-----------|----------|
| `llm_voice` | Gemini Live, Vapi, ElevenLabs, OpenAI Realtime, xAI Grok, Ultravox, Retell AI | Full duplex conversation |
| `voice_platform` | Vapi, ElevenLabs | Managed conversation platforms |
| `tts` | Edge TTS, OpenAI TTS, ElevenLabs, Gemini TTS, MiniMax TTS, Mistral TTS | Text → Speech |
| `stt` | Faster Whisper, OpenAI Whisper, Gemini STT | Speech → Text |

## CLI Management

```bash
# List all providers
sora voice providers list

# Enable/disable
sora voice providers enable gemini-live
sora voice providers disable vapi
sora voice providers enable openai-realtime
sora voice providers enable xai-grok
sora voice providers enable ultravox
sora voice providers enable retell

# Configure (interactive)
sora voice providers config edge-tts
sora voice providers config openai-realtime

# Quick-setup via setup wizard
sora setup --provider openai-realtime
```

## Configuration

```yaml
voice:
  providers:
    gemini_live:      { enabled: true,  configured: true,  type: llm_voice, model: gemini-3.1-flash-live-preview }
    vapi:             { enabled: false, configured: false, type: voice_platform }
    elevenlabs:       { enabled: false, configured: false, type: tts }
    openai_realtime:  { enabled: false, configured: false, type: llm_voice }
    xai_grok:         { enabled: false, configured: false, type: llm_voice }
    ultravox:         { enabled: false, configured: false, type: llm_voice }
    retell:           { enabled: false, configured: false, type: llm_voice }
    edge_tts:         { enabled: true,  configured: true,  type: tts }
    openai_tts:       { enabled: false, configured: false, type: tts }
    whisper:          { enabled: false, configured: false, type: stt }
```

## Runtime Switching

```python
# In chat, switch TTS provider
/tts edge-tts

# Switch STT
/stt whisper

# Switch LLM Voice
/voice gemini-live
/voice openai-realtime
/voice xai-grok
```

## Web Dashboard

The dashboard's **Providers** panel shows:
- All providers with enable/disable toggles
- Configuration status
- Real-time provider health
- One-click switching
