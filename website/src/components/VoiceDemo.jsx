import React, { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Volume2, VolumeX, Settings, CheckCircle, AlertCircle, Loader2, Zap, MessageSquare } from 'lucide-react'

export default function VoiceDemo({ status }) {
  const [isActive, setIsActive] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [provider, setProvider] = useState('gemini-live')
  const [logs, setLogs] = useState([])
  const [isConnecting, setIsConnecting] = useState(false)
  const visualizerRef = useRef(null)

  const providers = [
    { id: 'gemini-live', name: 'Gemini Live', desc: 'Google Multimodal Live API', color: '#4285F4' },
    { id: 'vapi', name: 'Vapi.ai', desc: 'Managed Voice Platform', color: '#00D4AA' },
    { id: 'elevenlabs', name: 'ElevenLabs', desc: 'Conversational AI Voices', color: '#FFFFFF' },
    { id: 'edge-tts', name: 'Edge TTS', desc: 'Free Microsoft Neural Voices', color: '#0078D4' },
  ]

  const addLog = (message, type = 'info') => {
    setLogs(prev => [...prev.slice(-49), { id: Date.now(), message, type, time: new Date().toLocaleTimeString() }])
  }

  const handleConnect = async () => {
    if (isConnecting) return
    setIsConnecting(true)
    addLog(`Connecting to ${providers.find(p => p.id === provider)?.name}...`, 'info')
    await new Promise(r => setTimeout(r, 1500))
    setIsActive(true)
    setIsConnecting(false)
    addLog(`Connected to ${providers.find(p => p.id === provider)?.name}`, 'success')
    if (visualizerRef.current) visualizerRef.current.classList.add('active')
  }

  const handleDisconnect = () => {
    setIsActive(false)
    setIsMuted(false)
    addLog('Disconnected', 'warning')
    if (visualizerRef.current) visualizerRef.current.classList.remove('active')
  }

  const handleMute = () => {
    setIsMuted(!isMuted)
    addLog(isMuted ? 'Microphone unmuted' : 'Microphone muted', isMuted ? 'success' : 'warning')
  }

  useEffect(() => {
    if (isActive) {
      const interval = setInterval(() => {
        if (Math.random() > 0.7) addLog('Processing audio...', 'info')
      }, 3000)
      return () => clearInterval(interval)
    }
  }, [isActive])

  const currentProvider = providers.find(p => p.id === provider)

  return (
    <div className="voice-demo">
      <div className="grid" style={{ gridTemplateColumns: '2fr 1fr 1fr', gap: '1rem' }}>
        <div className="card">
          <div className="card-title"><Mic size={20} /><span>Live Voice Demo</span></div>
          <div className="provider-selector">
            <label className="label">Voice Provider</label>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {providers.map(p => (
                <button key={p.id} className={`btn ${provider === p.id ? 'btn-primary' : 'btn-secondary'}`} style={{ borderColor: provider === p.id ? p.color : undefined }} onClick={() => setProvider(p.id)} disabled={isActive}>{p.name}</button>
              ))}
            </div>
            <p style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: 'var(--fg-muted)' }}>{currentProvider?.desc}</p>
          </div>
          <div className="voice-visualizer" ref={visualizerRef}>
            {[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15].map(i => <div key={i} className="bar" style={{ animationDelay: `${i * 0.05}s` }} />)}
          </div>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '1rem' }}>
            {!isActive && !isConnecting ? (
              <button className="btn btn-primary" onClick={handleConnect} style={{ flex: 1, minWidth: '180px' }}><Zap size={18} /><span>Connect to {currentProvider?.name}</span></button>
            ) : isConnecting ? (
              <button className="btn btn-primary" disabled style={{ flex: 1, minWidth: '180px' }}><Loader2 className="spinner" size={18} /><span>Connecting...</span></button>
            ) : (
              <>
                <button className="btn btn-secondary" onClick={handleMute} style={{ flex: 1, minWidth: '140px' }}>{isMuted ? <MicOff size={18} /> : <Mic size={18} />}<span>{isMuted ? 'Unmute' : 'Mute'}</span></button>
                <button className="btn btn-secondary" onClick={handleMute} style={{ flex: 1, minWidth: '140px' }}>{isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}<span>{isMuted ? 'Unmute Audio' : 'Mute Audio'}</span></button>
                <button className="btn btn-danger" onClick={handleDisconnect} style={{ flex: 1, minWidth: '140px' }}><AlertCircle size={18} /><span>Disconnect</span></button>
              </>
            )}
          </div>
          <div className="status-indicator" style={{ marginTop: '1rem' }}>
            <div className={`status-dot ${isActive ? 'online' : isConnecting ? 'connecting' : 'offline'}`} />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.875rem' }}>{isActive ? 'Connected' : isConnecting ? 'Connecting...' : 'Disconnected'}</span>
          </div>
        </div>
        <div className="card">
          <div className="card-title"><Zap size={20} /><span>Connection Status</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="status-item"><div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}><span style={{ color: 'var(--fg-muted)', fontSize: '0.875rem' }}>Provider</span><span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{currentProvider?.name}</span></div></div>
            <div className="status-item"><div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}><span style={{ color: 'var(--fg-muted)', fontSize: '0.875rem' }}>Status</span><span className={`badge ${isActive ? 'badge-online' : isConnecting ? 'badge-warning' : 'badge-offline'}`}>{isActive ? 'ONLINE' : isConnecting ? 'CONNECTING' : 'OFFLINE'}</span></div></div>
            <div className="status-item"><div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}><span style={{ color: 'var(--fg-muted)', fontSize: '0.875rem' }}>Latency</span><span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{isActive ? `${Math.floor(Math.random() * 100 + 50)}ms` : 'N/A'}</span></div></div>
            <div className="status-item"><div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}><span style={{ color: 'var(--fg-muted)', fontSize: '0.875rem' }}>Audio Quality</span><span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{isActive ? '48kHz Opus' : 'N/A'}</span></div></div>
            <div className="status-item"><div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}><span style={{ color: 'var(--fg-muted)', fontSize: '0.875rem' }}>Session Time</span><span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{isActive ? '00:00' : '00:00'}</span></div></div>
          </div>
          {status?.offline && <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,71,87,0.1)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--danger)' }}><div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--danger)' }}><AlertCircle size={18} /><span>S0RA CLI not running. Start with <code>sora chat</code> or <code>sora voice live</code></span></div></div>}
        </div>
        <div className="card">
          <div className="card-title"><Settings size={20} /><span>Quick Config</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div><label className="label">Discord Guild ID</label><input type="text" className="input" placeholder="123456789012345678" /></div>
            <div><label className="label">Voice Channel ID</label><input type="text" className="input" placeholder="123456789012345678" /></div>
            <div><label className="label">Gemini API Key</label><input type="password" className="input" placeholder="AIzaSy..." /></div>
            <div><label className="label">Vapi API Key</label><input type="password" className="input" placeholder="sk_..." /></div>
            <button className="btn btn-secondary" style={{ marginTop: '0.5rem' }}><CheckCircle size={16} /><span>Save & Connect</span></button>
          </div>
        </div>
      </div>
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-title"><MessageSquare size={20} /><span>Live Logs</span></div>
        <div className="code-block" style={{ maxHeight: '300px', overflow: 'auto' }}>
          {logs.length === 0 ? <div style={{ color: 'var(--fg-muted)', textAlign: 'center', padding: '2rem' }}>Connect to a voice provider to see live logs...</div> : logs.map(log => <div key={log.id} style={{ color: log.type === 'success' ? 'var(--accent)' : log.type === 'warning' ? 'var(--accent-warm)' : log.type === 'error' ? 'var(--danger)' : 'var(--fg)', margin: '0.25rem 0' }}><span style={{ color: 'var(--fg-muted)', marginRight: '0.5rem' }}>{log.time}</span><span>{log.message}</span></div>)}
        </div>
      </div>
    </div>
  )
}