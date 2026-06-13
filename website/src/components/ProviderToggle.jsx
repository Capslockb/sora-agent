import React, { useState } from 'react'
import { Cpu, ToggleRight, ToggleLeft, CheckCircle, AlertCircle, Loader2, ExternalLink } from 'lucide-react'

export default function ProviderToggle({ status }) {
  const [providers, setProviders] = useState([
    { id: 'gemini-live', name: 'Gemini Live', enabled: true, configured: false, description: 'Google\'s Multimodal Live API with native audio streaming. Low latency, high quality.', category: 'LLM Voice', docsUrl: 'https://ai.google.dev/gemini-api/docs/live' },
    { id: 'vapi', name: 'Vapi.ai', enabled: false, configured: false, description: 'Managed voice platform with WebSocket transport. Supports multiple TTS providers.', category: 'Voice Platform', docsUrl: 'https://docs.vapi.ai' },
    { id: 'elevenlabs', name: 'ElevenLabs', enabled: false, configured: false, description: 'High-quality conversational AI voices with emotional range. Credit-based billing.', category: 'TTS', docsUrl: 'https://elevenlabs.io/docs/conversational-ai' },
    { id: 'edge-tts', name: 'Edge TTS', enabled: true, configured: true, description: 'Free Microsoft neural voices. Good for testing and development.', category: 'TTS (Free)', docsUrl: 'https://github.com/rany2/edge-tts' },
    { id: 'openai-tts', name: 'OpenAI TTS', enabled: false, configured: false, description: 'OpenAI\'s text-to-speech models (tts-1, tts-1-hd). Requires API key.', category: 'TTS', docsUrl: 'https://platform.openai.com/docs/guides/text-to-speech' },
    { id: 'whisper', name: 'Whisper STT', enabled: false, configured: false, description: 'OpenAI Whisper for speech-to-text. Local or API.', category: 'STT', docsUrl: 'https://platform.openai.com/docs/guides/speech-to-text' },
  ])

  const toggleProvider = (id) => {
    setProviders(prev => prev.map(p => {
      if (p.id === id) {
        const newEnabled = !p.enabled
        if (newEnabled && !p.configured) {
          return { ...p, enabled: false } // Can't enable if not configured
        }
        return { ...p, enabled: newEnabled }
      }
      return p
    }))
  }

  const configureProvider = (id) => {
    // In real app, this would open a modal for API key entry
    alert(`Configure ${providers.find(p => p.id === id)?.name} - would open settings modal`)
  }

  return (
    <div className="providers-page">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ margin: '0 0 0.5rem', fontSize: '2rem', fontWeight: 700 }}>Voice Providers</h1>
        <p style={{ color: 'var(--fg-muted)', fontSize: '1.125rem' }}>Configure and toggle voice providers for your S0RA agent</p>
      </div>

      <div className="grid grid-2" style={{ gap: '1rem' }}>
        {providers.map(provider => (
          <div key={provider.id} className={`card provider-card ${provider.enabled ? 'active' : ''}`}>
            <div className="provider-header">
              <div>
                <div className="provider-name">{provider.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{provider.category}</div>
              </div>
              <div className="provider-status">
                <span className={`badge ${provider.enabled ? 'badge-online' : provider.configured ? 'badge-offline' : 'badge-warning'}`}>
                  {provider.enabled ? 'ENABLED' : provider.configured ? 'READY' : 'NOT CONFIGURED'}
                </span>
              </div>
            </div>
            <p style={{ color: 'var(--fg-muted)', fontSize: '0.875rem', marginBottom: '1rem' }}>{provider.description}</p>
            <div className="provider-actions" style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <button
                className={`btn ${provider.enabled ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => toggleProvider(provider.id)}
                disabled={!provider.configured}
                style={{ flex: 1, minWidth: '120px' }}
              >
                {provider.enabled ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
                <span>{provider.enabled ? 'Enabled' : provider.configured ? 'Enable' : 'Configure First'}</span>
              </button>
              {!provider.configured && (
                <button className="btn btn-secondary" onClick={() => configureProvider(provider.id)} style={{ flex: 1, minWidth: '120px' }}>
                  <Settings size={16} /> <span>Configure</span>
                </button>
              )}
              <a href={provider.docsUrl} target="_blank" rel="noopener noreferrer" className="btn btn-secondary" style={{ flex: 1, minWidth: '120px', textDecoration: 'none' }}>
                <ExternalLink size={16} /> <span>Docs</span>
              </a>
            </div>
            {provider.enabled && (
              <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'var(--accent-dim)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--accent)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem' }}>
                <CheckCircle size={14} style={{ color: 'var(--accent)' }}/>
                <span>Active provider — will be used for voice calls</span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="card" style={{ marginTop: '2rem' }}>
        <div className="card-title"><Cpu size={20} /><span>Provider Priority Order</span></div>
        <p style={{ color: 'var(--fg-muted)', marginBottom: '1rem' }}>Drag to reorder (enabled providers only). First available provider will be used.</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {providers.filter(p => p.enabled).map((provider, index) => (
            <div key={provider.id} className="card" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent)', minWidth: '2rem' }}>{index + 1}.</span>
              <span style={{ flex: 1 }}>{provider.name}</span>
              <span className="badge badge-online">{provider.category}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}