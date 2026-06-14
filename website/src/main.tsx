import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, Bot, BrainCircuit, Cable, Mic2, PhoneCall, Radio, RefreshCw, Sparkles } from 'lucide-react'
import {
  VoiceOrb,
  VoiceWave,
  VADIndicator,
  WaveformMini,
  useMicrophoneStream,
  useAudioAnalyser,
  useVoiceActivity,
  type VoiceState,
} from 'react-ai-voice-visualizer'
import './styles.css'

// ── S0RA backend types ──

type StatusPayload = {
  voice?: {
    status: string
    type: string
    model: string
    activeCalls: number
    llmProvider: string
    ttsProvider: string
    sttProvider: string
  }
  mcp?: { status: string; transport: string; port: number; clients: number }
  voip?: { status: string; ari: boolean; port: number; calls: number }
  system?: { status: string; platform: string; python: string }
}

type VisualizerPayload = {
  status: string
  timestamp: string
  pipeline: Array<{ id: string; label: string; state: string; detail: string }>
  providers: Array<{ id: string; label: string; category: string; configured: boolean; active: boolean }>
  audio: {
    inputLevel: number
    outputLevel: number
    sampleRate: number
    inputChunks: number
    outputChunks: number
  }
  call: { active: boolean; provider: string; channel: string; guild: string }
}

const fallbackStatus: StatusPayload = {
  voice: { status: 'offline', type: 'none', model: '—', activeCalls: 0, llmProvider: 'none', ttsProvider: 'none', sttProvider: 'none' },
  mcp: { status: 'unknown', transport: 'stdio', port: 3000, clients: 0 },
  voip: { status: 'unknown', ari: false, port: 5000, calls: 0 },
  system: { status: 'unknown', platform: 'unknown', python: 'unknown' },
}

// ── helpers ──

function apiBase() {
  const explicit = import.meta.env.VITE_SORA_API_BASE
  if (explicit) return explicit.replace(/\/$/, '')
  if (location.port === '3000' || location.port === '5173') return `${location.protocol}//${location.hostname}:8080`
  return ''
}

function voiceStateFromSora(
  callActive: boolean,
  micActive: boolean,
  voiceStatus: string,
): VoiceState {
  if (callActive) return 'speaking'
  if (micActive) return 'listening'
  if (voiceStatus === 'configured') return 'listening'
  return 'idle'
}

// ── S0RA data hook ──

function useSoraData() {
  const [status, setStatus] = useState<StatusPayload>(fallbackStatus)
  const [visualizer, setVisualizer] = useState<VisualizerPayload | null>(null)
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState(true)

  async function refresh() {
    try {
      const base = apiBase()
      const [statusRes, visualizerRes] = await Promise.all([
        fetch(`${base}/api/status`),
        fetch(`${base}/api/visualizer/state`),
      ])
      if (!statusRes.ok) throw new Error(`status HTTP ${statusRes.status}`)
      if (!visualizerRes.ok) throw new Error(`visualizer HTTP ${visualizerRes.status}`)
      setStatus(await statusRes.json())
      setVisualizer(await visualizerRes.json())
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
    const id = window.setInterval(refresh, 2500)
    return () => window.clearInterval(id)
  }, [])

  return { status, visualizer, error, loading, refresh }
}

// ── sub-components ──

function Pipeline({ visualizer }: { visualizer: VisualizerPayload | null }) {
  const pipeline = visualizer?.pipeline ?? [
    { id: 'discord', label: 'Discord Voice', state: 'waiting', detail: 'No API data yet' },
    { id: 'bridge', label: 'S0RA Bridge', state: 'waiting', detail: 'Awaiting backend' },
    { id: 'provider', label: 'Voice Provider', state: 'waiting', detail: 'Gemini / Vapi / ElevenLabs' },
    { id: 'speaker', label: 'Audio Return', state: 'waiting', detail: 'Playback pipeline' },
  ]
  return (
    <section className="panel pipeline-panel">
      <div className="panel-title"><Cable size={18} /> Voice pipeline</div>
      <div className="pipeline">
        {pipeline.map((step, index) => (
          <React.Fragment key={step.id}>
            <div className={`pipeline-step ${step.state}`}>
              <span className="step-index">{index + 1}</span>
              <strong>{step.label}</strong>
              <small>{step.detail}</small>
            </div>
            {index < pipeline.length - 1 && <div className="connector" />}
          </React.Fragment>
        ))}
      </div>
    </section>
  )
}

function ProviderGrid({ visualizer, status }: { visualizer: VisualizerPayload | null; status: StatusPayload }) {
  const providers = visualizer?.providers ?? [
    { id: 'gemini-live', label: 'Gemini Live', category: 'LLM Voice', configured: false, active: status.voice?.llmProvider === 'gemini-live' },
    { id: 'vapi', label: 'Vapi', category: 'LLM Voice', configured: false, active: status.voice?.llmProvider === 'vapi' },
    { id: 'elevenlabs', label: 'ElevenLabs', category: 'LLM Voice', configured: false, active: status.voice?.llmProvider === 'elevenlabs' },
    { id: 'voip', label: 'VOIP / Asterisk', category: 'Telephony', configured: Boolean(status.voip?.ari), active: status.voice?.llmProvider === 'voip' },
  ]
  return (
    <section className="panel">
      <div className="panel-title"><BrainCircuit size={18} /> Providers</div>
      <div className="provider-grid">
        {providers.map(provider => (
          <div key={provider.id} className={`provider-card ${provider.active ? 'active' : ''}`}>
            <div>
              <strong>{provider.label}</strong>
              <small>{provider.category}</small>
            </div>
            <span className={provider.configured ? 'pill ok' : 'pill muted'}>{provider.configured ? 'configured' : 'not set'}</span>
          </div>
        ))}
      </div>
    </section>
  )
}

function Metric({ label, value, icon }: { label: string; value: string | number; icon: React.ReactNode }) {
  return (
    <div className="metric">
      <div className="metric-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

// ── App ──

function App() {
  const { status, visualizer, error, loading, refresh } = useSoraData()

  // Library hooks — microphone + audio analysis
  const { stream, isActive: micActive, start: micStart, stop: micStop } = useMicrophoneStream()
  const { frequencyData, volume, timeDomainData } = useAudioAnalyser(stream, {
    fftSize: 256,
    smoothingTimeConstant: 0.8,
  })
  const { isSpeaking } = useVoiceActivity(volume, {
    volumeThreshold: 0.08,
    silenceThreshold: 1200,
  })

  // Derived state
  const callActive = visualizer?.call.active || false
  const voiceStatus = status.voice?.status ?? 'stopped'
  const voiceState = voiceStateFromSora(callActive, micActive, voiceStatus)
  const provider = status.voice?.llmProvider ?? 'none'

  return (
    <main className="app-shell">
      <div className="orb orb-a" />
      <div className="orb orb-b" />

      {/* header */}
      <header className="hero">
        <div>
          <div className="eyebrow"><Sparkles size={16} /> S0RA voice companion</div>
          <h1>Voice Visualizer</h1>
          <p>Live control surface for Hermes-facing voice bridges — Gemini Live, Vapi, ElevenLabs, VOIP.</p>
        </div>
        <div className="hero-actions">
          {micActive ? (
            <button className="mic-button" onClick={micStop}>
              <Mic2 size={16} /> Stop mic
            </button>
          ) : (
            <button className="mic-button" onClick={micStart}>
              <Mic2 size={16} /> Enable mic
            </button>
          )}
          <button className="refresh" onClick={refresh} disabled={loading}>
            <RefreshCw size={16} /> Refresh
          </button>
        </div>
      </header>

      {/* alerts */}
      {error && <div className="alert">Backend unreachable: {error}. Showing local fallback.</div>}

      {/* ── VOICE VISUALIZER (the actual voice part) ── */}
      <section className="visualizer-card">
        <div className="visual-core">
          {/* Hero visual — VoiceOrb from react-ai-voice-visualizer */}
          <VoiceOrb
            audioData={frequencyData}
            volume={volume}
            state={voiceState}
            size={220}
            primaryColor="#06B6D4"
            secondaryColor="#8B5CF6"
            glowIntensity={0.7}
            noiseScale={0.18}
            noiseSpeed={0.55}
            onClick={micActive ? micStop : micStart}
          />

          {/* Metadata column */}
          <div>
            <div className="visual-meta">
              <VADIndicator
                state={
                  micActive && isSpeaking ? 'speaking'
                  : micActive ? 'listening'
                  : callActive ? 'speaking'
                  : voiceStatus === 'configured' ? 'idle'
                  : 'idle'
                }
                size="md"
                showLabel
              />

              <h2>{provider}</h2>
              <p>{status.voice?.model ?? 'No model selected'}</p>

              <div className="mic-strip">
                <span>Mic</span>
                <strong>{micActive ? 'active' : 'idle'}</strong>
              </div>

              <div className="mic-strip">
                <span>Volume</span>
                <strong>{Math.round(volume * 100)}%</strong>
              </div>

              {micActive && (
                <div className="mic-strip">
                  <span>Speaking</span>
                  <strong>{isSpeaking ? 'yes 🔊' : 'no'}</strong>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Waveform — VoiceWave from library (replaces the old fake bars) */}
        <div className="waveform">
          {micActive ? (
            <VoiceWave
              audioData={frequencyData}
              volume={volume}
              state={voiceState}
              size={280}
              lineColor="#62eaff"
              numberOfLines={5}
              lineWidth={2}
              phaseShift={0.15}
            />
          ) : (
            <WaveformMini
              audioData={frequencyData}
              volume={volume}
              barCount={16}
              width={280}
              height={40}
              color="#62eaff"
            />
          )}
        </div>
      </section>

      {/* metrics row */}
      <section className="metrics-grid">
        <Metric label="Voice" value={status.voice?.status ?? 'unknown'} icon={<Mic2 size={20} />} />
        <Metric label="MCP" value={`${status.mcp?.transport ?? 'stdio'}:${status.mcp?.port ?? 0}`} icon={<Bot size={20} />} />
        <Metric label="VOIP" value={status.voip?.status ?? 'unknown'} icon={<PhoneCall size={20} />} />
        <Metric label="System" value={status.system?.python ?? 'unknown'} icon={<Activity size={20} />} />
      </section>

      {/* pipeline + providers */}
      <div className="two-column">
        <Pipeline visualizer={visualizer} />
        <ProviderGrid visualizer={visualizer} status={status} />
      </div>

      {/* footer */}
      <footer>
        <Radio size={14} /> API: {apiBase() || 'same-origin'} · Last sample: {visualizer?.timestamp ?? 'not connected'}
      </footer>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
