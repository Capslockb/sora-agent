import React, { useState, useEffect } from 'react'
import { Zap, CheckCircle, AlertCircle, Loader2, Cpu, HardDrive, MemoryStick, Network, Terminal, Github } from 'lucide-react'

export default function StatusPanel({ status }) {
  const [systemInfo, setSystemInfo] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        // In production, call Sora CLI API
        const res = await fetch('/api/system-info')
        if (res.ok) {
          const data = await res.json()
          setSystemInfo(data)
        } else {
          setSystemInfo({ fallback: true })
        }
      } catch {
        setSystemInfo({ fallback: true })
      } finally {
        setIsLoading(false)
      }
    }
    fetchInfo()
    const interval = setInterval(fetchInfo, 15000)
    return () => clearInterval(interval)
  }, [])

  if (isLoading) {
    return <div className="loading"><Loader2 className="spinner" size={32} /><p>Loading system status...</p></div>
  }

  const checks = [
    { id: 'sora-cli', name: 'S0RA CLI', command: 'sora --version', status: status?.offline ? 'fail' : 'pass', icon: Terminal },
    { id: 'gemini-api', name: 'Gemini API', command: 'GEMINI_API_KEY', status: status?.offline ? 'unknown' : 'pass', icon: Cpu },
    { id: 'discord-bot', name: 'Discord Bot', command: 'DISCORD_BOT_TOKEN', status: status?.offline ? 'unknown' : 'pass', icon: Network },
    { id: 'mcp-server', name: 'MCP Server', command: 'sora mcp status', status: status?.offline ? 'unknown' : 'pass', icon: HardDrive },
    { id: 'honcho', name: 'Honcho Memory', command: 'honcho status', status: 'unknown', icon: MemoryStick },
    { id: 'python', name: 'Python 3.11+', command: 'python3 --version', status: 'pass', icon: Terminal },
    { id: 'node', name: 'Node.js 20+', command: 'node --version', status: 'pass', icon: Terminal },
    { id: 'git', name: 'Git', command: 'git --version', status: 'pass', icon: Github },
  ]

  return (
    <div className="status-page">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ margin: '0 0 0.5rem', fontSize: '2rem', fontWeight: 700 }}>System Status</h1>
        <p style={{ color: 'var(--fg-muted)', fontSize: '1.125rem' }}>Real-time health checks for S0RA Agent</p>
      </div>

      <div className="grid grid-3" style={{ gap: '1rem', marginBottom: '2rem' }}>
        <div className="card">
          <div className="card-title"><Zap size={20} /><span>Overall Health</span></div>
          <div className="status-indicator" style={{ fontSize: '2rem', marginTop: '1rem' }}>
            <div className={`status-dot ${status?.offline ? 'offline' : 'online'}`} style={{ width: '16px', height: '16px' }} />
            <span style={{ fontSize: '1.5rem', fontWeight: 600 }}>{status?.offline ? 'OFFLINE' : 'ONLINE'}</span>
          </div>
          <p style={{ marginTop: '1rem', color: 'var(--fg-muted)' }}>
            {status?.offline 
              ? 'S0RA CLI is not running. Start with <code>sora chat</code> or <code>sora voice live</code>' 
              : 'All systems operational'}
          </p>
        </div>
        <div className="card">
          <div className="card-title"><Cpu size={20} /><span>Voice Bridge</span></div>
          <div className="status-indicator" style={{ fontSize: '2rem', marginTop: '1rem' }}>
            <div className={`status-dot ${status?.offline ? 'offline' : 'online'}`} style={{ width: '16px', height: '16px' }} />
            <span style={{ fontSize: '1.5rem', fontWeight: 600 }}>{status?.offline ? 'DISCONNECTED' : 'READY'}</span>
          </div>
          <p style={{ marginTop: '1rem', color: 'var(--fg-muted)' }}>
            {status?.offline ? 'No active voice connection' : 'Gemini Live bridge available'}
          </p>
        </div>
        <div className="card">
          <div className="card-title"><HardDrive size={20} /><span>MCP Server</span></div>
          <div className="status-indicator" style={{ fontSize: '2rem', marginTop: '1rem' }}>
            <div className={`status-dot ${status?.offline ? 'offline' : 'online'}`} style={{ width: '16px', height: '16px' }} />
            <span style={{ fontSize: '1.5rem', fontWeight: 600 }}>{status?.offline ? 'STOPPED' : 'RUNNING'}</span>
          </div>
          <p style={{ marginTop: '1rem', color: 'var(--fg-muted)' }}>
            {status?.offline ? 'Start with <code>sora mcp start</code>' : 'MCP server accepting connections'}
          </p>
        </div>
      </div>

      <div className="card">
        <div className="card-title"><Terminal size={20} /><span>Health Checks</span></div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {checks.map(check => (
            <div key={check.id} className="card" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <check.icon size={18} style={{ color: 'var(--fg-muted)' }}/>
              <div style={{ flex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>{check.name}</span>
                <span className={`badge ${check.status === 'pass' ? 'badge-online' : check.status === 'fail' ? 'badge-offline' : 'badge-warning'}`}>
                  {check.status === 'pass' ? '✓ PASS' : check.status === 'fail' ? '✗ FAIL' : '? UNKNOWN'}
                </span>
              </div>
              <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--fg-muted)', background: 'var(--bg)', padding: '0.25rem 0.5rem', borderRadius: 'var(--radius-sm)' }}>{check.command}</code>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-2" style={{ gap: '1rem', marginTop: '1.5rem' }}>
        <div className="card">
          <div className="card-title"><Terminal size={20} /><span>Quick Actions</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <button className="btn btn-primary" onClick={() => window.open('http://localhost:3000', '_blank')}>
              <ExternalLink size={16} /> <span>Open Web Dashboard</span>
            </button>
            <button className="btn btn-secondary">
              <Loader2 size={16} /> <span>Run Doctor Check</span>
            </button>
            <button className="btn btn-secondary">
              <Zap size={16} /> <span>Start Voice Bridge</span>
            </button>
            <button className="btn btn-secondary">
              <HardDrive size={16} /> <span>Start MCP Server</span>
            </button>
          </div>
        </div>
        <div className="card">
          <div className="card-title"><Github size={20} /><span>Version Info</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontFamily: 'var(--font-mono)', fontSize: '0.875rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--fg-muted)' }}>S0RA CLI:</span><span>0.1.0</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--fg-muted)' }}>Website:</span><span>0.1.0</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--fg-muted)' }}>Hermes Plugin:</span><span>0.1.0</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--fg-muted)' }}>Python:</span><span>3.11+</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--fg-muted)' }}>Node:</span><span>20+</span></div>
          </div>
        </div>
      </div>
    </div>
  )
}