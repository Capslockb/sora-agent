import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
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

type MicStatus = 'idle' | 'requesting' | 'active' | 'denied' | 'error' | 'unsupported'

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

function useMicrophoneVisualizer() {
  const [status, setStatus] = useState<MicStatus>('idle')
  const [error, setError] = useState('')
  const [levels, setLevels] = useState<number[]>(() => seededWave(0).map(v => v / 100))
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const frameRef = useRef<number | null>(null)

  const stop = useCallback(() => {
    if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current)
    frameRef.current = null
    streamRef.current?.getTracks().forEach(track => track.stop())
    streamRef.current = null
    analyserRef.current?.disconnect()
    analyserRef.current = null
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => undefined)
    }
    audioContextRef.current = null
    setStatus('idle')
    setError('')
    setLevels(seededWave(0).map(v => v / 100))
  }, [])

  const start = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setStatus('unsupported')
      setError('Browser does not expose navigator.mediaDevices.getUserMedia')
      return
    }

    setStatus('requesting')
    setError('')
    try {
      const stream = await Promise.race([
        navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            sampleRate: 16000,
          },
        }),
        new Promise<never>((_, reject) => window.setTimeout(() => reject(new Error('Microphone permission request timed out')), 10000)),
      ])

      streamRef.current = stream
      const AudioCtx = window.AudioContext || window.webkitAudioContext
      const context = new AudioCtx()
      if (context.state === 'suspended') await context.resume()
      const analyser = context.createAnalyser()
      analyser.fftSize = 128
      analyser.smoothingTimeConstant = 0.78
      const source = context.createMediaStreamSource(stream)
      source.connect(analyser)
      audioContextRef.current = context
      analyserRef.current = analyser
      setStatus('active')

      const data = new Uint8Array(analyser.frequencyBinCount)
      const draw = () => {
        analyser.getByteFrequencyData(data)
        const next = Array.from({ length: 44 }, (_, index) => {
          const sample = data[Math.floor(index * data.length / 44)] ?? 0
          return Math.max(0.08, Math.min(1, sample / 255))
        })
        setLevels(next)
        frameRef.current = window.requestAnimationFrame(draw)
      }
      draw()
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      setStatus(message.includes('denied') || message.includes('NotAllowed') ? 'denied' : 'error')
      setError(message)
    }
  }, [])

  useEffect(() => () => stop(), [stop])

  return { status, error, levels, start, stop }
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

function Waveform({ active, level, levels }: { active: boolean; level: number; levels?: number[] }) {
  const [tick, setTick] = useState(0)
  useEffect(() => {
    const id = window.setInterval(() => setTick(t => t + 1), active ? 120 : 420)
    return () => window.clearInterval(id)
  }, [active])
  const bars = useMemo(() => levels?.map(v => Math.round(v * 100)) ?? seededWave(tick * (active ? 9 : 2)), [tick, active, levels])
  return (
    <div className="waveform" aria-label="voice waveform visualizer">
      {bars.map((height, i) => (
        <span
          key={i}
          style={{ height: `${Math.max(10, height * (levels ? 1 : active ? Math.max(level, 0.22) : 0.2))}%`, animationDelay: `${i * 18}ms` }}
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
  const mic = useMicrophoneVisualizer()
  const voiceActive = visualizer?.call.active || status.voice?.status === 'configured'
  const outputLevel = visualizer?.audio.outputLevel ?? 0.45
  const micActive = mic.status === 'active'
  const waveformLevels = micActive ? mic.levels : undefined

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
        <div className="hero-actions">
          <button className="mic-button" onClick={micActive ? mic.stop : mic.start} disabled={mic.status === 'requesting'}>
            <Mic2 size={16} /> {mic.status === 'requesting' ? 'Requesting mic…' : micActive ? 'Stop mic preview' : 'Enable mic preview'}
          </button>
          <button className="refresh" onClick={refresh} disabled={loading}>
            <RefreshCw size={16} /> Refresh
          </button>
        </div>
      </header>

      {error && <div className="alert">Backend unreachable: {error}. Showing local fallback visualizer.</div>}
      {mic.error && <div className="alert">Mic preview unavailable: {mic.error}</div>}

      <section className="visualizer-card">
        <div className="visual-core">
          <div className={`pulse-ring ${voiceActive ? 'active' : ''}`}>
            <Waves size={84} />
          </div>
          <div>
            <span className="status-dot"><i className={voiceActive || micActive ? 'on' : ''} /> {micActive ? 'browser mic live' : voiceActive ? 'voice path configured' : 'standing by'}</span>
            <h2>{status.voice?.llmProvider ?? 'none'}</h2>
            <p>{micActive ? 'Local browser microphone preview via getUserMedia + AnalyserNode' : status.voice?.model ?? 'No model selected'}</p>
            <div className="mic-strip">
              <span>Mic permission</span>
              <strong>{mic.status}</strong>
            </div>
          </div>
        </div>
        <Waveform active={Boolean(voiceActive || micActive)} level={outputLevel} levels={waveformLevels} />
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
