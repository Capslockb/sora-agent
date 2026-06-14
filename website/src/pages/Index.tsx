import { useState, useEffect, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { Activity, Bot, BrainCircuit, Cable, Mic2, PhoneCall, Radio, RefreshCw } from 'lucide-react';
import { VoiceVisualizer } from '@/components/voice/VoiceVisualizer';
import { VoiceButton } from '@/components/voice/VoiceButton';
import { BackgroundEffects } from '@/components/BackgroundEffects';
import { cn } from '@/lib/utils';

// ── S0RA backend types ──

type StatusPayload = {
  voice?: { status: string; type: string; model: string; activeCalls: number; llmProvider: string; ttsProvider: string; sttProvider: string };
  mcp?: { status: string; transport: string; port: number; clients: number };
  voip?: { status: string; ari: boolean; port: number; calls: number };
  system?: { status: string; platform: string; python: string };
};

type VisualizerPayload = {
  status: string;
  timestamp: string;
  pipeline: Array<{ id: string; label: string; state: string; detail: string }>;
  providers: Array<{ id: string; label: string; category: string; configured: boolean; active: boolean }>;
  audio: { inputLevel: number; outputLevel: number; sampleRate: number; inputChunks: number; outputChunks: number };
  call: { active: boolean; provider: string; channel: string; guild: string };
};

type MicState = 'idle' | 'requesting' | 'connected' | 'speaking' | 'error';

const FALLBACK_STATUS: StatusPayload = {
  voice: { status: 'offline', type: 'none', model: '—', activeCalls: 0, llmProvider: 'none', ttsProvider: 'none', sttProvider: 'none' },
  mcp: { status: 'unknown', transport: 'stdio', port: 3000, clients: 0 },
  voip: { status: 'unknown', ari: false, port: 5000, calls: 0 },
  system: { status: 'unknown', platform: 'unknown', python: 'unknown' },
};

// ── API helper ──

function apiBase() {
  const explicit = (import.meta as any).env?.VITE_SORA_API_BASE;
  if (explicit) return explicit.replace(/\/$/, '');
  if (location.port === '3000' || location.port === '5173' || location.port === '8082')
    return `${location.protocol}//${location.hostname}:8080`;
  return '';
}

// ── S0RA data hook ──

function useSoraData() {
  const [status, setStatus] = useState<StatusPayload>(FALLBACK_STATUS);
  const [visualizer, setVisualizer] = useState<VisualizerPayload | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const base = apiBase();
      const [sRes, vRes] = await Promise.all([
        fetch(`${base}/api/status`),
        fetch(`${base}/api/visualizer/state`),
      ]);
      if (!sRes.ok) throw new Error(`status ${sRes.status}`);
      if (!vRes.ok) throw new Error(`visualizer ${vRes.status}`);
      setStatus(await sRes.json());
      setVisualizer(await vRes.json());
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 2500);
    return () => clearInterval(id);
  }, [refresh]);

  return { status, visualizer, error, loading, refresh };
}

// ── Browser microphone hook ──

function useBrowserMic() {
  const [micState, setMicState] = useState<MicState>('idle');
  const [micError, setMicError] = useState('');
  const [frequencyData, setFrequencyData] = useState<Uint8Array>(new Uint8Array(64));
  const [volume, setVolume] = useState(0);
  const streamRef = useRef<MediaStream | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const frameRef = useRef<number | null>(null);
  const volHistoryRef = useRef<number[]>([]);

  const cleanup = useCallback(() => {
    if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    frameRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    analyserRef.current?.disconnect();
    analyserRef.current = null;
    ctxRef.current?.close().catch(() => {});
    ctxRef.current = null;
  }, []);

  const start = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setMicState('error');
      setMicError('getUserMedia not available');
      return;
    }
    setMicState('requesting');
    setMicError('');
    try {
      const stream = await Promise.race([
        navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, sampleRate: 16000 } }),
        new Promise<never>((_, reject) => setTimeout(() => reject(new Error('Mic permission timed out')), 10000)),
      ]);
      streamRef.current = stream;
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      if (ctx.state === 'suspended') await ctx.resume();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 128;
      analyser.smoothingTimeConstant = 0.8;
      ctx.createMediaStreamSource(stream).connect(analyser);
      ctxRef.current = ctx;
      analyserRef.current = analyser;
      setMicState('connected');

      const data = new Uint8Array(analyser.frequencyBinCount);
      const draw = () => {
        analyser.getByteFrequencyData(data);
        setFrequencyData(new Uint8Array(data));

        let sum = 0;
        for (let i = 0; i < data.length; i++) sum += data[i] * data[i];
        const rms = Math.sqrt(sum / data.length) / 255;
        volHistoryRef.current.push(rms);
        if (volHistoryRef.current.length > 10) volHistoryRef.current.shift();
        const avgVol = volHistoryRef.current.reduce((a, b) => a + b, 0) / volHistoryRef.current.length;
        setVolume(avgVol);
        setMicState(avgVol > 0.04 ? 'speaking' : 'connected');

        frameRef.current = requestAnimationFrame(draw);
      };
      draw();
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setMicState(msg.includes('denied') || msg.includes('NotAllowed') ? 'error' : 'error');
      setMicError(msg);
    }
  }, []);

  const stop = useCallback(() => {
    cleanup();
    setMicState('idle');
    setFrequencyData(new Uint8Array(64));
    setVolume(0);
  }, [cleanup]);

  useEffect(() => () => cleanup(), [cleanup]);

  return { micState, micError, frequencyData, volume, start, stop };
}

// ── Sub-components ──

function Pipeline({ visualizer }: { visualizer: VisualizerPayload | null }) {
  const pipeline = visualizer?.pipeline ?? [
    { id: 'discord', label: 'Discord Voice', state: 'waiting', detail: 'No API data yet' },
    { id: 'bridge', label: 'S0RA Bridge', state: 'waiting', detail: 'Awaiting backend' },
    { id: 'provider', label: 'Voice Provider', state: 'waiting', detail: 'Gemini / Vapi / ElevenLabs' },
    { id: 'speaker', label: 'Audio Return', state: 'waiting', detail: 'Playback pipeline' },
  ];
  return (
    <section className="glass-enhanced rounded-2xl p-5">
      <div className="flex items-center gap-2 text-zinc-200 font-semibold mb-4"><Cable size={18} /> Voice pipeline</div>
      <div className="grid grid-cols-4 gap-2.5">
        {pipeline.map((step, i) => (
          <div key={step.id} className={cn(
            'min-h-[120px] p-3.5 rounded-xl border flex flex-col gap-2',
            step.state === 'configured' || step.state === 'active' || step.state === 'ready'
              ? 'border-emerald-500/30 bg-emerald-500/5'
              : 'border-white/8 bg-white/4'
          )}>
            <span className="w-7 h-7 grid place-items-center rounded-full bg-cyan-400/10 text-cyan-300 font-bold text-xs">{i + 1}</span>
            <strong className="text-sm">{step.label}</strong>
            <small className="text-zinc-500 leading-relaxed">{step.detail}</small>
          </div>
        ))}
      </div>
    </section>
  );
}

function ProviderGrid({ visualizer, status }: { visualizer: VisualizerPayload | null; status: StatusPayload }) {
  const providers = visualizer?.providers ?? [
    { id: 'gemini-live', label: 'Gemini Live', category: 'LLM Voice', configured: false, active: status.voice?.llmProvider === 'gemini-live' },
    { id: 'vapi', label: 'Vapi', category: 'LLM Voice', configured: false, active: status.voice?.llmProvider === 'vapi' },
    { id: 'elevenlabs', label: 'ElevenLabs', category: 'LLM Voice', configured: false, active: status.voice?.llmProvider === 'elevenlabs' },
    { id: 'voip', label: 'VOIP / Asterisk', category: 'Telephony', configured: Boolean(status.voip?.ari), active: status.voice?.llmProvider === 'voip' },
  ];
  return (
    <section className="glass-enhanced rounded-2xl p-5">
      <div className="flex items-center gap-2 text-zinc-200 font-semibold mb-4"><BrainCircuit size={18} /> Providers</div>
      <div className="flex flex-col gap-2.5">
        {providers.map((p) => (
          <div key={p.id} className={cn('flex items-center justify-between gap-3 p-3.5 rounded-xl border transition-colors',
            p.active ? 'border-cyan-400/40 shadow-[inset_0_0_28px_hsla(187,100%,57%,0.08)]' : 'border-white/8 bg-white/4'
          )}>
            <div>
              <strong className="text-sm">{p.label}</strong>
              <small className="block text-zinc-500">{p.category}</small>
            </div>
            <span className={cn('text-xs px-2 py-1 rounded-full', p.configured ? 'bg-emerald-500/10 text-emerald-300' : 'bg-white/7 text-zinc-500')}>
              {p.configured ? 'configured' : 'not set'}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

function Metric({ label, value, icon }: { label: string; value: string | number; icon: React.ReactNode }) {
  return (
    <div className="glass-enhanced rounded-2xl p-4 grid grid-cols-[auto_1fr] gap-x-3 gap-y-2 items-center">
      <div className="row-span-2 w-10 h-10 grid place-items-center rounded-xl bg-cyan-400/8 text-cyan-300">{icon}</div>
      <span className="text-zinc-500 text-xs">{label}</span>
      <strong className="truncate">{value}</strong>
    </div>
  );
}

// ── Main Page ──

export const Index = () => {
  const { status, visualizer, error: soraError, loading, refresh } = useSoraData();
  const { micState, micError, frequencyData, volume, start: micStart, stop: micStop } = useBrowserMic();

  const callActive = visualizer?.call.active || false;
  const micActive = micState === 'connected' || micState === 'speaking';
  const isSpeaking = micState === 'speaking';

  return (
    <div className="min-h-screen bg-[#09090b] relative overflow-hidden film-grain">
      <BackgroundEffects />

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="flex items-center gap-3">
            <div className="relative w-8 h-8 flex items-center justify-center">
              <div className="absolute inset-0 rounded-lg bg-cyan-400/10 border border-cyan-400/20" />
              <motion.div className="w-2 h-2 rounded-full bg-cyan-400" animate={{ scale: [1, 1.2, 1], opacity: [0.8, 1, 0.8] }} transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }} />
            </div>
            <span className="font-display text-lg text-zinc-200 tracking-tight">S0RA<span className="text-cyan-400"> Voice</span></span>
          </motion.div>

          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex items-center gap-3">
            <button onClick={refresh} disabled={loading} className="p-2 rounded-lg bg-zinc-900/50 border border-zinc-800/50 text-zinc-400 hover:text-zinc-200 transition-colors">
              <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            </button>
          </motion.div>
        </div>
      </header>

      {/* Main content */}
      <main className="relative z-10 min-h-screen">
        <div className="max-w-5xl mx-auto px-6 pt-32 pb-20">
          {/* Hero */}
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} className="text-center mb-16">
            <span className="font-mono text-xs tracking-[0.3em] uppercase text-cyan-400/80">Voice Orchestration</span>
            <h1 className="font-display text-5xl sm:text-6xl md:text-7xl leading-tight tracking-tight mt-4 mb-6">
              <span className="text-gradient">Speak with S0RA</span>
            </h1>
            <p className="text-zinc-400 text-lg max-w-xl mx-auto leading-relaxed">
              Live control surface for Hermes-facing voice bridges — Gemini Live, Vapi, ElevenLabs, VOIP.
            </p>
          </motion.div>

          {/* Voice interaction zone */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }} className="flex flex-col items-center gap-8 mb-16">
            <VoiceButton
              size="lg"
              state={micActive ? micState : soraError ? 'error' : micState}
              errorMessage={micActive ? undefined : soraError || undefined}
              onToggle={micActive ? micStop : micStart}
            />

            {/* Status text */}
            <div className="text-center">
              <p className="text-zinc-500 text-sm font-mono">
                {soraError ? `Backend: ${soraError}` : micError ? micError : micActive ? 'Microphone active — waveform live below' : 'Click the mic to preview your voice'}
              </p>
              {micActive && (
                <div className="flex items-center justify-center gap-6 mt-3">
                  <span className="text-xs text-zinc-500">Volume <strong className="text-cyan-300">{Math.round(volume * 100)}%</strong></span>
                  <span className="text-xs text-zinc-500">Provider <strong className="text-purple-300">{status.voice?.llmProvider ?? 'none'}</strong></span>
                </div>
              )}
            </div>

            {/* Voice waveform */}
            <div className="w-full max-w-2xl">
              <VoiceVisualizer
                frequencyData={frequencyData}
                isActive={micActive || callActive}
                isSpeaking={isSpeaking}
                barCount={64}
                responsive
              />
            </div>
          </motion.div>

          {/* Metrics row */}
          <div className="grid grid-cols-4 gap-3 mb-6">
            <Metric label="Voice" value={status.voice?.status ?? 'unknown'} icon={<Mic2 size={18} />} />
            <Metric label="MCP" value={`${status.mcp?.transport ?? 'stdio'}:${status.mcp?.port ?? 0}`} icon={<Bot size={18} />} />
            <Metric label="VOIP" value={status.voip?.status ?? 'unknown'} icon={<PhoneCall size={18} />} />
            <Metric label="System" value={status.system?.python ?? 'unknown'} icon={<Activity size={18} />} />
          </div>

          {/* Pipeline + Providers */}
          <div className="grid grid-cols-[1.15fr_0.85fr] gap-4">
            <Pipeline visualizer={visualizer} />
            <ProviderGrid visualizer={visualizer} status={status} />
          </div>

          {/* Footer */}
          <div className="mt-6 flex items-center gap-2 text-zinc-600 text-xs">
            <Radio size={12} /> API: {apiBase() || 'same-origin'} · {visualizer?.timestamp ?? 'not connected'}
          </div>
        </div>
      </main>
    </div>
  );
};
