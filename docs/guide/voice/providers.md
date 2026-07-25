# Provider Management

S0RA contains provider definitions for **TTS**, **STT**, and **LLM voice**, but provider management is not currently unified.

## Status

**EXPERIMENTAL — two divergent command surfaces.**

The repository exposes both:

```bash
sora providers ...
sora voice providers ...
```

They use different registries, configuration shapes, and disable semantics. A change made through one surface may not be reflected by the other, the setup wizard, dashboard/API, or runtime consumers. See [Issue #15](https://github.com/Capslockb/sora-agent/issues/15).

## Declared provider catalog

The broader top-level registry declares these categories:

| Type | Providers |
|------|-----------|
| `llm_voice` | Gemini Live, Vapi, ElevenLabs, OpenAI Realtime, xAI Grok, Ultravox, Retell AI |
| `tts` | Edge TTS, OpenAI TTS, ElevenLabs TTS, Gemini TTS, MiniMax TTS, Mistral TTS |
| `stt` | Faster Whisper, OpenAI Whisper, Gemini STT |

This catalog is not proof that every provider is enabled, configured, or connected to a working live bridge.

## Top-level commands

```bash
sora providers list
sora providers status
sora providers enable gemini-live
sora providers disable llm_voice
sora providers config edge-tts
```

Current behavior:

- `enable` selects a provider for its category.
- `disable` resets an entire category, not an individual provider.
- `config` runs the interactive provider configuration flow.
- TTS and STT selection use category paths such as `voice.tts.provider` and `voice.stt.provider`.
- LLM-voice selection and display currently use inconsistent configuration paths, so list/status output may not reflect the last enable operation.

## Nested voice commands

```bash
sora voice providers list
sora voice providers enable gemini-live
sora voice providers disable vapi
sora voice providers config edge-tts
```

Current behavior:

- This surface toggles entries under `voice.providers` rather than selecting the category paths used by the top-level command.
- Its default registry contains only Gemini Live, Vapi, ElevenLabs, Edge TTS, OpenAI TTS, and Whisper.
- Providers advertised by the parser, including OpenAI Realtime, xAI, Ultravox, and Retell, can be rejected as unknown unless they already exist in `voice.providers`.
- `config` is a placeholder that directs the operator to `sora setup`; it does not configure the provider.
- This surface has no `status` subcommand.

## Safe operator guidance

Until Issue #15 is resolved:

1. Use `sora setup` or `sora setup --provider <name>` for initial configuration.
2. Treat both provider command families as experimental management surfaces.
3. Do not assume an enable/disable result proves that the runtime, dashboard, or the other command family selected the same provider.
4. Inspect the resulting non-secret configuration and run provider-specific validation before starting a bridge.
5. Keep API keys in protected environment or configuration sources; do not place secrets in ordinary command arguments or shared logs.

## Required validation before unified status

Provider management should be described as unified only after:

- one canonical provider registry and configuration schema is selected;
- both command paths are true aliases or one is explicitly deprecated;
- list, status, enable, disable, and configure have consistent semantics;
- setup, dashboard/API, Hermes tools, and runtime consumers read the same state;
- existing configuration is migrated without losing settings or credentials;
- exact-head tests pass after pytest CI is activated under Issue #12.
