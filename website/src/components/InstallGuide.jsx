import React, { useState } from 'react'
import { Download, Terminal, CheckCircle, AlertCircle, Loader2, Github, ArrowRight, Copy, Zap } from 'lucide-react'

export default function InstallGuide() {
  const [step, setStep] = useState(0)
  const [method, setMethod] = useState('pipx')
  const [copied, setCopied] = useState(null)

  const steps = [
    { id: 0, title: 'Choose Install Method', desc: 'Select your preferred package manager' },
    { id: 1, title: 'Run Install Command', desc: 'Execute the command in your terminal' },
    { id: 2, title: 'Run Setup Wizard', desc: 'Configure S0RA with interactive setup' },
    { id: 3, title: 'Start Voice Bridge', desc: 'Connect to Discord and start talking' },
    { id: 4, title: 'Verify Installation', desc: 'Run health checks and test voice' },
  ]

  const installCommands = {
    pipx: 'pipx install git+https://github.com/capslockb/sora-agent',
    uv: 'uv pip install git+https://github.com/capslockb/sora-agent',
    pip: 'pip install git+https://github.com/capslockb/sora-agent',
    docker: 'docker run -it --rm -v ~/.sora:/root/.sora ghcr.io/capslockb/sora-agent:latest',
  }

  const copyCommand = (cmd) => {
    navigator.clipboard.writeText(cmd)
    setCopied(cmd)
    setTimeout(() => setCopied(null), 2000)
  }

  const currentCommand = installCommands[method]

  return (
    <div className="install-page">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ margin: '0 0 0.5rem', fontSize: '2rem', fontWeight: 700 }}>Install S0RA Agent</h1>
        <p style={{ color: 'var(--fg-muted)', fontSize: '1.125rem' }}>Get up and running in under 2 minutes</p>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        {steps.map((s, i) => (
          <div key={s.id} className={`card ${i <= step ? 'active' : ''}`} style={{ flex: 1, minWidth: '160px', padding: '1rem', textAlign: 'center', position: 'relative' }}>
            <div style={{ 
              width: '32px', height: '32px', borderRadius: '50%', margin: '0 auto 0.5rem',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: i < step ? 'var(--accent)' : i === step ? 'var(--accent-dim)' : 'var(--border)',
              border: i === step ? '2px solid var(--accent)' : 'none',
              color: i <= step ? '#0a0a0f' : 'var(--fg-muted)',
              fontWeight: 700, fontSize: '0.875rem',
              transition: 'all var(--transition)'
            }}>
              {i < step ? <CheckCircle size={16} /> : i + 1}
            </div>
            <div style={{ fontWeight: 600, fontSize: '0.875rem', color: i <= step ? 'var(--fg)' : 'var(--fg-muted)' }}>{s.title}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--fg-muted)', marginTop: '0.25rem' }}>{s.desc}</div>
            {i < steps.length - 1 && (
              <div style={{ position: 'absolute', top: '16px', right: '-50%', width: '100%', height: '2px', background: i < step ? 'var(--accent)' : 'var(--border)', zIndex: -1 }} />
            )}
          </div>
        ))}
      </div>

      <div className="card" style={{ maxWidth: '800px' }}>
        <div className="card-title">
          <Zap size={20} />
          <span>Step {step + 1} of {steps.length}: {steps[step].title}</span>
        </div>
        <p style={{ color: 'var(--fg-muted)', marginBottom: '1.5rem' }}>{steps[step].desc}</p>

        {step === 0 && (
          <div>
            <label className="label">Installation Method</label>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              {Object.entries(installCommands).map(([key, cmd]) => (
                <button
                  key={key}
                  className={`btn ${method === key ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setMethod(key)}
                  style={{ flex: 1, minWidth: '160px', padding: '1.5rem', textAlign: 'left' }}
                >
                  <div style={{ fontWeight: 600, marginBottom: '0.5rem', textTransform: 'capitalize' }}>{key}</div>
                  <code style={{ fontSize: '0.7rem', color: 'var(--fg-muted)' }}>{cmd.slice(0, 50)}...</code>
                </button>
              ))}
            </div>
            <button className="btn btn-primary" style={{ marginTop: '1.5rem', width: '100%' }} onClick={() => setStep(1)}>
              <ArrowRight size={18} /> <span>Continue to Installation</span>
            </button>
          </div>
        )}

        {step === 1 && (
          <div>
            <div className="code-block" style={{ position: 'relative' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--fg-muted)' }}>$ </span>
                <button className="btn btn-secondary btn-sm" onClick={() => copyCommand(currentCommand)}>
                  {copied === currentCommand ? <CheckCircle size={14} /> : <Copy size={14} />}
                  <span>{copied === currentCommand ? 'Copied!' : 'Copy'}</span>
                </button>
              </div>
              <code>{currentCommand}</code>
            </div>
            <p style={{ marginTop: '1rem', color: 'var(--fg-muted)', fontSize: '0.875rem' }}>
              Run this command in your terminal. Installation takes ~30-60 seconds.
            </p>
            <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
              <button className="btn btn-secondary" onClick={() => setStep(0)}><ArrowRight size={18} style={{ transform: 'rotate(180deg)' }} /> <span>Back</span></button>
              <button className="btn btn-primary" onClick={() => setStep(2)}><span>Installation Complete</span> <ArrowRight size={18} /></button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div>
            <div className="code-block">
              <code>$ sora setup</code>
            </div>
            <p style={{ marginTop: '1rem', color: 'var(--fg-muted)' }}>
              The interactive setup wizard will guide you through:
            </p>
            <ul style={{ marginTop: '1rem', paddingLeft: '1.5rem', color: 'var(--fg-muted)', lineHeight: 2 }}>
              <li>Model provider selection (Ollama, OpenRouter, Anthropic, etc.)</li>
              <li>Discord bot configuration (token, guild, channel)</li>
              <li>Voice provider setup (Gemini Live, Vapi, ElevenLabs, Edge TTS)</li>
              <li>MCP server configuration</li>
              <li>Memory system (Honcho local/cloud)</li>
              <li>Tools (TTS, STT, Web search, Image generation)</li>
              <li>OpenWakeWord for "Hey Sora" wake word (optional)</li>
            </ul>
            <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
              <button className="btn btn-secondary" onClick={() => setStep(1)}><ArrowRight size={18} style={{ transform: 'rotate(180deg)' }} /> <span>Back</span></button>
              <button className="btn btn-primary" onClick={() => setStep(3)}><span>Setup Complete</span> <ArrowRight size={18} /></button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <div className="code-block">
              <code>$ sora voice live --guild YOUR_GUILD_ID --channel YOUR_CHANNEL_ID</code>
            </div>
            <p style={{ marginTop: '1rem', color: 'var(--fg-muted)' }}>
              Or use the Vapi bridge:
            </p>
            <div className="code-block" style={{ marginTop: '0.5rem' }}>
              <code>$ sora voice vapi --guild YOUR_GUILD_ID --channel YOUR_CHANNEL_ID</code>
            </div>
            <p style={{ marginTop: '1rem', color: 'var(--fg-muted)' }}>
              The bridge will connect to Discord and start streaming audio through Gemini Live.
            </p>
            <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
              <button className="btn btn-secondary" onClick={() => setStep(2)}><ArrowRight size={18} style={{ transform: 'rotate(180deg)' }} /> <span>Back</span></button>
              <button className="btn btn-primary" onClick={() => setStep(4)}><span>Bridge Connected</span> <ArrowRight size={18} /></button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div>
            <div className="code-block" style={{ marginBottom: '0.5rem' }}>
              <code>$ sora doctor</code>
            </div>
            <div className="code-block" style={{ marginBottom: '0.5rem' }}>
              <code>$ sora status</code>
            </div>
            <div className="code-block">
              <code>$ sora mcp status</code>
            </div>
            <p style={{ marginTop: '1rem', color: 'var(--fg-muted)' }}>
              All checks should pass. If any fail, run <code>sora doctor</code> for detailed diagnostics.
            </p>
            <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
              <button className="btn btn-secondary" onClick={() => setStep(3)}><ArrowRight size={18} style={{ transform: 'rotate(180deg)' }} /> <span>Back</span></button>
              <a href="https://github.com/capslockb/sora-agent" target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                <Github size={18} /> <span>View on GitHub</span>
              </a>
            </div>
            <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'var(--accent-dim)', borderRadius: 'var(--radius)', border: '1px solid var(--accent)' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                <CheckCircle size={20} style={{ color: 'var(--accent)', flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <h3 style={{ margin: '0 0 0.5rem', color: 'var(--accent)' }}>Installation Complete!</h3>
                  <p style={{ margin: 0, color: 'var(--fg)', fontSize: '0.875rem' }}>
                    You're ready to use S0RA Agent. Join our <a href="https://discord.gg/sora-agent" target="_blank" style={{ color: 'var(--accent)' }}>Discord</a> for support and updates.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-2" style={{ gap: '1rem', marginTop: '2rem' }}>
        <div className="card">
          <div className="card-title"><Terminal size={20} /><span>Requirements</span></div>
          <ul style={{ lineHeight: 2, color: 'var(--fg-muted)' }}>
            <li>Python 3.11+</li>
            <li>Node.js 20+ (for website/dashboard)</li>
            <li>Git</li>
            <li>Discord Bot Token (for voice)</li>
            <li>Gemini API Key (for Gemini Live)</li>
            <li>Vapi API Key (optional, for Vapi bridge)</li>
          </ul>
        </div>
        <div className="card">
          <div className="card-title"><Github size={20} /><span>Links</span></div>
          <ul style={{ lineHeight: 2 }}>
            <li><a href="https://github.com/capslockb/sora-agent" target="_blank">GitHub Repository</a></li>
            <li><a href="https://docs.sora-agent.dev" target="_blank">Documentation</a></li>
            <li><a href="https://discord.gg/sora-agent" target="_blank">Discord Community</a></li>
            <li><a href="https://github.com/capslockb/sora-agent/issues" target="_blank">Report Issues</a></li>
          </ul>
        </div>
      </div>
    </div>
  )
}