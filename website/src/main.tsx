import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, Bot, BrainCircuit, Cable, Mic2, PhoneCall, Radio, RefreshCw, Sparkles, Waves } from 'lucide-react'
import './styles.css'

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
  system: { status: 'unknown', platform: 'unknown', python: 'unknown' }
}

function apiBase() {
  const explicit = import.meta.env.VITE_SORA_API_BASE
  if (explicit) return explicit.replace(/\/$/, '')
  if (location.port === '3000' || location.port === '5173') return `${location.protocol}//${location.hostname}:8080`
  return ''
}

function seededWave(seed: number, count = 44) {
  return Array.from({ length: count }, (_, index) => {
    const x = index + seed / 180
    const primary = Math.sin(x * 0.72) * 0.5 + 0.5
    const secondary = Math.sin(x * 1.87 + 1.4) * 0.5 + 0.5
    return Math.max(14, Math.round((primary * 0.65 + secondary * 0.35) * 92))
  })
}

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
        fetch(`${base}/api/visualizer/state`)
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

function Waveform({ active, level }: { active: boolean; level: number }) {
  const [tick, setTick] = useState(0)
  useEffect(() => {
    const id = window.setInterval(() => setTick(t => t + 1), active ? 120 : 420)
    return () => window.clearInterval(id)
  }, [active])
  const bars = useMemo(() => seededWave(tick * (active ? 9 : 2)), [tick, active])
  return (
    <div className="waveform" aria-label="voice waveform visualizer">
      {bars.map((height, i) => (
        <span
          key={i}
          style={{ height: `${Math.max(10, height * (active ? Math.max(level, 0.22) : 0.2))}%`, animationDelay: `${i * 18}ms` }}
        />
      ))}
    </div>
  )
}

function Pipeline({ visualizer }: { visualizer: VisualizerPayload | null }) {
  const pipeline = visualizer?.pipeline ?? [
    { id: 'discord', label: 'Discord Voice', state: 'waiting', detail: 'No API data yet' },
    { id: 'bridge', label: 'S0RA Bridge', state: 'waiting', detail: 'Awaiting backend' },
    { id: 'provider', label: 'Voice Provider', state: 'waiting', detail: 'Gemini / Vapi / ElevenLabs' },
    { id: 'speaker', label: 'Audio Return', state: 'waiting', detail: 'Playback pipeline' }
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
    { id: 'voip', label: 'VOIP', category: 'Telephony', configured: Boolean(status.voip?.ari), active: status.voice?.llmProvider === 'voip' }
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

function App() {
  const { status, visualizer, error, loading, refresh } = useSoraData()
  const voiceActive = visualizer?.call.active || status.voice?.status === 'configured'
  const outputLevel = visualizer?.audio.outputLevel ?? 0.45

  return (
    <main className="app-shell">
      <div className="orb orb-a" />
      <div className="orb orb-b" />

      <header className="hero">
        <div>
          <div className="eyebrow"><Sparkles size={16} /> S0RA voice companion</div>
          <h1>Voice Visualizer Web UI</h1>
          <p>Live control surface for Hermes-facing voice bridges: Discord, Gemini Live, Vapi, ElevenLabs, and VOIP.</p>
        </div>
        <button className="refresh" onClick={refresh} disabled={loading}>
          <RefreshCw size={16} /> Refresh
        </button>
      </header>

      {error && <div className="alert">Backend unreachable: {error}. Showing local fallback visualizer.</div>}

      <section className="visualizer-card">
        <div className="visual-core">
          <div className={`pulse-ring ${voiceActive ? 'active' : ''}`}>
            <Waves size={84} />
          </div>
          <div>
            <span className="status-dot"><i className={voiceActive ? 'on' : ''} /> {voiceActive ? 'voice path configured' : 'standing by'}</span>
            <h2>{status.voice?.llmProvider ?? 'none'}</h2>
            <p>{status.voice?.model ?? 'No model selected'}</p>
          </div>
        </div>
        <Waveform active={Boolean(voiceActive)} level={outputLevel} />
      </section>

      <section className="metrics-grid">
        <Metric label="Voice" value={status.voice?.status ?? 'unknown'} icon={<Mic2 size={20} />} />
        <Metric label="MCP" value={`${status.mcp?.transport ?? 'stdio'}:${status.mcp?.port ?? 0}`} icon={<Bot size={20} />} />
        <Metric label="VOIP" value={status.voip?.status ?? 'unknown'} icon={<PhoneCall size={20} />} />
        <Metric label="System" value={status.system?.python ?? 'unknown'} icon={<Activity size={20} />} />
      </section>

      <div className="two-column">
        <Pipeline visualizer={visualizer} />
        <ProviderGrid visualizer={visualizer} status={status} />
      </div>

      <footer>
        <Radio size={14} /> API: {apiBase() || 'same-origin'} · Last sample: {visualizer?.timestamp ?? 'not connected'}
      </footer>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
