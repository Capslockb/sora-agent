# Voice Visualizer Web UI research notes

This page captures the web-research baseline for S0RA's browser-side voice visualizer.

## Fit checks

- [`YZarytskyi/react-voice-visualizer`](https://github.com/YZarytskyi/react-voice-visualizer) — React hook/component library for audio recording and real-time visualization with the Web Audio API. Useful reference for recorder-control state, but heavier than S0RA needs right now.
- [`openai/realtime-voice-component`](https://github.com/openai/realtime-voice-component) — production-oriented voice widget patterns. Relevant lesson: if a voice widget stays idle, inspect browser media/WebRTC support and permission state first.
- [`Louis-Mascari/MangoWave`](https://github.com/Louis-Mascari/MangoWave) — browser audio-reactive visualizer using `getUserMedia` plus `AnalyserNode`; good reference for direct microphone-driven visual feedback.
- Twilio's [Audio visualisation with the Web Audio API and React](https://www.twilio.com/en-us/blog/developers/tutorials/building-blocks/audio-visualisation-web-audio-api--react) — confirms the core pattern: microphone `MediaStream` -> `AudioContext` -> `MediaStreamSource` -> `AnalyserNode` -> rendered waveform data.
- CallSphere's [Building a Voice UI for AI Agents](https://callsphere.ai/blog/building-voice-ui-ai-agents-microphone-waveform-playback) — voice-agent UI pattern: request microphone permission explicitly, track `idle/requesting/active/denied/error`, use `getUserMedia` constraints such as echo cancellation/noise suppression, and render real-time waveform feedback.

## Decision

Do not vendor a full recorder package yet. S0RA needs a Hermes-facing status/visualizer, not an isolated recorder product. The current UI therefore implements a lightweight local microphone preview:

1. user clicks **Enable mic preview**;
2. browser asks for microphone permission via `navigator.mediaDevices.getUserMedia`;
3. Web Audio `AnalyserNode` converts live microphone energy into waveform bars;
4. the permission state is visible in the UI and failure is non-fatal.

This keeps the visualizer aligned with S0RA's role: observing and testing voice surfaces, while the actual Discord/Gemini/Vapi/ElevenLabs bridges remain backend/provider-owned.
