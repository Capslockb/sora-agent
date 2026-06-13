import React, { useState, useEffect } from 'react'
import { Mic, Settings, Terminal, Zap, Layers, CheckCircle, AlertCircle, Loader2, Play, Pause, MessageSquare, Cpu, Github } from 'lucide-react'
import VoiceDemo from './components/VoiceDemo'
import ProviderToggle from './components/ProviderToggle'
import StatusPanel from './components/StatusPanel'
import InstallGuide from './components/InstallGuide'
import './styles/index.css'

function App() {
  const [activeTab, setActiveTab] = useState('demo')
  const [systemStatus, setSystemStatus] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchSystemStatus()
    const interval = setInterval(fetchSystemStatus, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchSystemStatus = async () => {
    try {
      // In production, this would call the Sora CLI API
      const res = await fetch('/api/status')
      if (res.ok) {
        const data = await res.json()
        setSystemStatus(data)
      } else {
        setSystemStatus({ error: 'Status endpoint not available' })
      }
    } catch {
      setSystemStatus({ offline: true })
    } finally {
      setIsLoading(false)
    }
  }

  const tabs = [
    { id: 'demo', label: 'Live Demo', icon: Mic },
    { id: 'providers', label: 'Providers', icon: Cpu },
    { id: 'status', label: 'Status', icon: Zap },
    { id: 'install', label: 'Install', icon: Terminal },
    { id: 'docs', label: 'Docs', icon: MessageSquare },
  ]

  return (
    <div className="sora-app">
      <header className="sora-header">
        <div className="logo">
          <Zap className="logo-icon" size={28} />
          <span className="logo-text">S0RA</span>
          <span className="logo-sub">Agent</span>
        </div>
        <nav className="tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.icon size={18} />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
        <a href="https://github.com/capslockb/sora-agent" target="_blank" rel="noopener noreferrer" className="github-link">
          <Github size={20} />
        </a>
      </header>

      <main className="sora-main">
        {isLoading ? (
          <div className="loading">
            <Loader2 className="spinner" size={32} />
            <p>Loading S0RA system status...</p>
          </div>
        ) : (
          <>
            {activeTab === 'demo' && <VoiceDemo status={systemStatus} />}
            {activeTab === 'providers' && <ProviderToggle status={systemStatus} />}
            {activeTab === 'status' && <StatusPanel status={systemStatus} />}
            {activeTab === 'install' && <InstallGuide />}
            {activeTab === 'docs' && <Documentation />}
          </>
        )}
      </main>

      <footer className="sora-footer">
        <p>S0RA Agent v0.1.0 — Voice-first AI with Gemini Live, Vapi, and MCP</p>
        <div className="links">
          <a href="https://github.com/capslockb/sora-agent" target="_blank">GitHub</a>
          <a href="https://docs.sora-agent.dev" target="_blank">Documentation</a>
          <a href="https://discord.gg/sora-agent" target="_blank">Discord</a>
        </div>
      </footer>
    </div>
  )
}

function Documentation() {
  return (
    <div className="docs-page">
      <h1>Documentation</h1>
      <div className="doc-sections">
        <section>
          <h2>Quick Start</h2>
          <pre><code>{`# Install
pipx install git+https://github.com/capslockb/sora-agent

# Or with uv
uv pip install git+https://github.com/capslockb/sora-agent

# Run setup wizard
sora setup

# Start voice bridge
sora voice live --guild YOUR_GUILD_ID --channel YOUR_CHANNEL_ID`}</code></pre>
        </section>
        <section>
          <h2>CLI Commands</h2>
          <table>
            <thead><tr><th>Command</th><th>Description</th></tr></thead>
            <tbody>
              <tr><td><code>sora chat</code></td><td>Interactive chat session</td></tr>
              <tr><td><code>sora setup</code></td><td>Interactive setup wizard</td></tr>
              <tr><td><code>sora voice live</code></td><td>Start Gemini Live bridge</td></tr>
              <tr><td><code>sora voice vapi</code></td><td>Start Vapi.ai bridge</td></tr>
              <tr><td><code>sora voice status</code></td><td>Show bridge status</td></tr>
              <tr><td><code>sora mcp start</code></td><td>Start MCP server</td></tr>
              <tr><td><code>sora status</code></td><td>System health dashboard</td></tr>
              <tr><td><code>sora doctor</code></td><td>Check dependencies</td></tr>
              <tr><td><code>sora config</code></td><td>Configuration management</td></tr>
            </tbody>
          </table>
        </section>
        <section>
          <h2>Voice Providers</h2>
          <ul>
            <li><strong>Gemini Live</strong> — Google's multimodal live API with native audio streaming</li>
            <li><strong>Vapi.ai</strong> — Managed voice platform with ElevenLabs TTS</li>
            <li><strong>ElevenLabs</strong> — High-quality conversational AI voices</li>
            <li><strong>Edge TTS</strong> — Free Microsoft neural voices</li>
          </ul>
        </section>
      </div>
    </div>
  )
}

export default App
