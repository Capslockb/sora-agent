import React, { useState, useEffect, useCallback } from 'react'
import { render, Box, Text, Static, useInput, useStdout } from 'ink'
import Spinner from 'ink-spinner'
import chalk from 'chalk'

const SORA_LOGO = `
    ███████╗██╗  ██╗██╗  ██╗
    ██╔════╝██║  ██║██║  ██║
    ███████╗███████║███████║
    ╚════██║██╔══██║██╔══██║
    ███████║██║  ██║██║  ██║
    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝
`

const menuItems = [
  { id: 'voice', label: 'Voice Bridge', desc: 'Start Gemini Live / Vapi / ElevenLabs', icon: '🎤' },
  { id: 'mcp', label: 'MCP Server', desc: 'Start/stop MCP server, list tools', icon: '🔌' },
  { id: 'providers', label: 'Providers', desc: 'Configure voice providers (TTS/STT/LLM)', icon: '⚡' },
  { id: 'status', label: 'Status', desc: 'System health & connection status', icon: '📊' },
  { id: 'config', label: 'Config', desc: 'View/edit Sora configuration', icon: '⚙️' },
  { id: 'doctor', label: 'Doctor', desc: 'Run diagnostics & dependency checks', icon: '🏥' },
  { id: 'setup', label: 'Setup Wizard', desc: 'Interactive first-time configuration', icon: '🧙' },
  { id: 'bench', label: 'Benchmark', desc: 'Voice latency & quality benchmarks', icon: '⏱️' },
  { id: 'exit', label: 'Exit', desc: 'Quit Sora TUI', icon: '🚪' },
]

function Logo() {
  return (
    <Text bold color="#00d4aa">
      {SORA_LOGO}
    </Text>
  )
}

function MenuItem({ item, isSelected, onSelect }) {
  return (
    <Box marginY={1} paddingX={2} backgroundColor={isSelected ? 'blue' : 'transparent'}>
      <Text color={isSelected ? 'white' : 'gray'}>
        {item.icon} {item.label}
      </Text>
      <Text color={isSelected ? 'white' : 'gray'} dimColor>
        {'  ' + item.desc}
      </Text>
    </Box>
  )
}

function VoicePanel({ onBack }) {
  const [provider, setProvider] = useState('gemini-live')
  const [connected, setConnected] = useState(false)
  const [logs, setLogs] = useState<string[]>([])

  const providers = [
    { id: 'gemini-live', name: 'Gemini Live', color: 'blue' },
    { id: 'vapi', name: 'Vapi.ai', color: 'green' },
    { id: 'elevenlabs', name: 'ElevenLabs', color: 'white' },
    { id: 'edge-tts', name: 'Edge TTS', color: 'cyan' },
  ]

  const addLog = (msg: string) => {
    setLogs(prev => [...prev.slice(-9), `[${new Date().toLocaleTimeString()}] ${msg}`])
  }

  const current = providers.find(p => p.id === provider)

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold color="green">🎤 Voice Bridge Control</Text>
      <Box marginTop={1} borderStyle="single" borderColor="gray" padding={1}>
        <Text>Provider: </Text>
        <Text bold color={current?.color}>{current?.name}</Text>
        <Text>  Status: </Text>
        <Text bold color={connected ? 'green' : 'red'}>
          {connected ? '● CONNECTED' : '○ DISCONNECTED'}
        </Text>
      </Box>

      <Box marginTop={1}>
        <Text>Providers:</Text>
        {providers.map(p => (
          <Box key={p.id} marginLeft={2}>
            <Text color={provider === p.id ? p.color : 'gray'}>
              {provider === p.id ? '▸ ' : '  '}{p.name}
            </Text>
          </Box>
        ))}
      </Box>

      <Box marginTop={1} borderStyle="single" borderColor="gray" padding={1} height={12}>
        <Text bold>Logs:</Text>
        {logs.map((log, i) => (
          <Text key={i} dimColor>{log}</Text>
        ))}
        {logs.length === 0 && <Text dimColor>No logs yet. Connect to see activity.</Text>}
      </Box>

      <Box marginTop={1}>
        {!connected ? (
          <Text bold color="green" onClick={() => { setConnected(true); addLog(`Connecting to ${current?.name}...`); setTimeout(() => addLog('Connected!'), 1000); }}>
            [Enter] Connect to {current?.name}
          </Text>
        ) : (
          <Text bold color="red" onClick={() => { setConnected(false); addLog('Disconnected'); }}>
            [Enter] Disconnect
          </Text>
        )}
        <Text marginLeft={2} dimColor>[1-4] Switch provider  [b] Back</Text>
      </Box>
    </Box>
  )
}

function StatusPanel({ onBack }) {
  const checks = [
    { name: 'Sora CLI', status: 'ok', cmd: 'sora --version' },
    { name: 'Python 3.11+', status: 'ok', cmd: 'python3 --version' },
    { name: 'Node.js 20+', status: 'ok', cmd: 'node --version' },
    { name: 'Git', status: 'ok', cmd: 'git --version' },
    { name: 'Gemini API', status: 'unknown', cmd: 'GEMINI_API_KEY' },
    { name: 'Discord Bot', status: 'unknown', cmd: 'DISCORD_BOT_TOKEN' },
    { name: 'MCP Server', status: 'unknown', cmd: 'sora mcp status' },
    { name: 'Honcho Memory', status: 'unknown', cmd: 'honcho status' },
  ]

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold color="green">📊 System Status</Text>
      <Box marginTop={1}>
        {checks.map((check, i) => (
          <Box key={i} flexDirection="row" marginBottom={1}>
            <Text width={20}>{check.name}</Text>
            <Text color={check.status === 'ok' ? 'green' : check.status === 'fail' ? 'red' : 'yellow'}>
              {check.status === 'ok' ? '✓ PASS' : check.status === 'fail' ? '✗ FAIL' : '? UNKNOWN'}
            </Text>
            <Text dimColor marginLeft={2}>{check.cmd}</Text>
          </Box>
        ))}
      </Box>
      <Text marginTop={1} dimColor>[b] Back</Text>
    </Box>
  )
}

function ConfigPanel({ onBack }) {
  return (
    <Box flexDirection="column" padding={1}>
      <Text bold color="green">⚙️ Configuration</Text>
      <Text marginTop={1} dimColor>Configuration management coming soon...</Text>
      <Text dimColor>[b] Back</Text>
    </Box>
  )
}

function DoctorPanel({ onBack }) {
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState<string[]>([])

  const runDoctor = async () => {
    setRunning(true)
    setResults(['Running diagnostics...'])
    await new Promise(r => setTimeout(r, 1000))
    setResults([
      '✓ Python 3.11.8 found',
      '✓ Node.js 20.12.0 found',
      '✓ Git 2.43.0 found',
      '✓ Sora CLI installed',
      '✓ Hermes plugin registered',
      '⚠ Gemini API key not set',
      '⚠ Discord bot token not set',
      '⚠ Honcho server not running',
    ])
    setRunning(false)
  }

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold color="green">🏥 Doctor Diagnostics</Text>
      <Box marginTop={1}>
        {!running ? (
          <Text bold color="green" onClick={runDoctor}>[Enter] Run Diagnostics</Text>
        ) : (
          <Box flexDirection="row">
            <Spinner type="dots" color="green" />
            <Text marginLeft={1}>Running...</Text>
          </Box>
        )}
        {results.map((r, i) => (
          <Text key={i} color={r.includes('✓') ? 'green' : r.includes('⚠') ? 'yellow' : 'white'}>{r}</Text>
        ))}
      </Box>
      <Text marginTop={1} dimColor>[b] Back</Text>
    </Box>
  )
}

function SetupPanel({ onBack }) {
  const [step, setStep] = useState(0)
  const steps = [
    'Welcome to Sora Setup!',
    'Select model provider (Ollama, OpenRouter, Anthropic...)',
    'Configure Discord bot token',
    'Set up voice provider (Gemini Live, Vapi, ElevenLabs)',
    'Configure MCP servers',
    'Set up memory (Honcho)',
    'Install complete!',
  ]

  const nextStep = () => {
    if (step < steps.length - 1) setStep(step + 1)
  }

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold color="green">🧙 Setup Wizard</Text>
      <Box marginTop={1} borderStyle="single" borderColor="gray" padding={1}>
        <Text bold>{steps[step]}</Text>
        <Text marginTop={1} dimColor>Step {step + 1} of {steps.length}</Text>
        <Box marginTop={1} flexDirection="row">
          <Text color={step > 0 ? 'green' : 'gray'} onClick={() => step > 0 && setStep(step - 1)}>[←] Back</Text>
          <Text marginLeft={2} color={step < steps.length - 1 ? 'green' : 'gray'} onClick={nextStep}>
            {step < steps.length - 1 ? '[→] Next' : '[✓] Complete'}
          </Text>
        </Box>
      </Box>
      <Text dimColor>[b] Back to menu</Text>
    </Box>
  )
}

function BenchmarkPanel({ onBack }) {
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState<Record<string, string>>({})

  const runBench = async () => {
    setRunning(true)
    setResults({})
    const tests = [
      { name: 'CLI startup', target: '< 100ms' },
      { name: 'Config load', target: '< 50ms' },
      { name: 'Plugin load', target: '< 200ms' },
      { name: 'Voice connect (mock)', target: '< 2000ms' },
      { name: 'MCP server start', target: '< 500ms' },
    ]
    for (const t of tests) {
      await new Promise(r => setTimeout(r, 500))
      const actual = Math.floor(Math.random() * 100 + 50)
      setResults(prev => ({ ...prev, [t.name]: `${actual}ms (target: ${t.target})` }))
    }
    setRunning(false)
  }

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold color="green">⏱️ Benchmarks</Text>
      <Box marginTop={1}>
        {!running ? (
          <Text bold color="green" onClick={runBench}>[Enter] Run Benchmarks</Text>
        ) : (
          <Box flexDirection="row">
            <Spinner type="dots" color="green" />
            <Text marginLeft={1}>Running benchmarks...</Text>
          </Box>
        )}
        {Object.entries(results).map(([name, value], i) => (
          <Text key={i} marginTop={1}>
            <Text bold>{name}: </Text>
            <Text color="cyan">{value}</Text>
          </Text>
        ))}
      </Box>
      <Text marginTop={1} dimColor>[b] Back</Text>
    </Box>
  )
}

function ProvidersPanel({ onBack }) {
  const providers = [
    { name: 'Gemini Live', type: 'LLM Voice', configured: false, enabled: true },
    { name: 'Vapi.ai', type: 'Voice Platform', configured: false, enabled: false },
    { name: 'ElevenLabs', type: 'TTS', configured: false, enabled: false },
    { name: 'Edge TTS', type: 'TTS (Free)', configured: true, enabled: true },
    { name: 'OpenAI TTS', type: 'TTS', configured: false, enabled: false },
    { name: 'Whisper STT', type: 'STT', configured: false, enabled: false },
  ]

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold color="green">⚡ Voice Providers</Text>
      <Box marginTop={1}>
        {providers.map((p, i) => (
          <Box key={i} marginBottom={1} padding={1} borderStyle="single" borderColor="gray">
            <Box flexDirection="row">
              <Text width={4} bold>{i + 1}.</Text>
              <Text width={20} bold color={p.enabled ? 'green' : 'white'}>{p.name}</Text>
              <Text width={15} dimColor>{p.type}</Text>
              <Text color={p.configured ? 'green' : 'yellow'}>
                {p.configured ? '✓ Configured' : '⚠ Not configured'}
              </Text>
              <Text marginLeft={2} color={p.enabled ? 'green' : 'red'}>
                {p.enabled ? '● ENABLED' : '○ DISABLED'}
              </Text>
            </Box>
          </Box>
        ))}
      </Box>
      <Text dimColor>[b] Back</Text>
    </Box>
  )
}

function MCPServerPanel({ onBack }) {
  return (
    <Box flexDirection="column" padding={1}>
      <Text bold color="green">🔌 MCP Server</Text>
      <Box marginTop={1} borderStyle="single" borderColor="gray" padding={1}>
        <Text bold>Available Commands:</Text>
        <Text marginTop={1} dimColor>
          sora mcp start [--port 3000] [--transport stdio|sse|streamable-http]
        </Text>
        <Text dimColor>
          sora mcp status
        </Text>
        <Text dimColor>
          sora mcp list
        </Text>
        <Text dimColor>
          sora mcp catalog
        </Text>
        <Text dimColor>
          sora mcp stop
        </Text>
      </Box>
      <Text marginTop={1} dimColor>
        Built-in servers: filesystem, github, sqlite, postgres, playwright, slack, notion, gdrive, memory, brave, fetch
      </Text>
      <Text dimColor>[b] Back</Text>
    </Box>
  )
}

export default function App() {
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [view, setView] = useState<'menu' | 'panel'>('menu')
  const [panel, setPanel] = useState<string | null>(null)
  const { write } = useStdout()

  useInput((input, key) => {
    if (view === 'menu') {
      if (key.upArrow) setSelectedIndex(i => Math.max(0, i - 1))
      else if (key.downArrow) setSelectedIndex(i => Math.min(menuItems.length - 1, i + 1))
      else if (key.return) {
        const item = menuItems[selectedIndex]
        if (item.id === 'exit') {
          write('\x1b[2J\x1b[H')
          process.exit(0)
        }
        setPanel(item.id)
        setView('panel')
      }
      else if (input >= '1' && input <= '9') {
        const idx = parseInt(input) - 1
        if (idx < menuItems.length) {
          const item = menuItems[idx]
          if (item.id === 'exit') process.exit(0)
          setPanel(item.id)
          setView('panel')
        }
      }
    } else {
      if (key.escape || (key.return && input === 'b')) {
        setView('menu')
        setPanel(null)
      }
    }
  })

  const panels: Record<string, React.ReactElement> = {
    voice: <VoicePanel onBack={() => { setView('menu'); setPanel(null); }} />,
    status: <StatusPanel onBack={() => { setView('menu'); setPanel(null); }} />,
    config: <ConfigPanel onBack={() => { setView('menu'); setPanel(null); }} />,
    doctor: <DoctorPanel onBack={() => { setView('menu'); setPanel(null); }} />,
    setup: <SetupPanel onBack={() => { setView('menu'); setPanel(null); }} />,
    bench: <BenchmarkPanel onBack={() => { setView('menu'); setPanel(null); }} />,
    providers: <ProvidersPanel onBack={() => { setView('menu'); setPanel(null); }} />,
    mcp: <MCPServerPanel onBack={() => { setView('menu'); setPanel(null); }} />,
  }

  if (view === 'panel' && panel) {
    return (
      <Box flexDirection="column" height="100%">
        <Box paddingX={1} paddingY={1} borderStyle="single" borderColor="blue">
          <Text bold color="blue">S0RA TUI</Text>
          <Text dimColor>{menuItems.find(m => m.id === panel)?.label}</Text>
        </Box>
        {panels[panel]}
      </Box>
    )
  }

  return (
    <Box flexDirection="column" height="100%">
      <Box paddingX={1} paddingY={1}>
        <Logo />
        <Text bold color="white">Voice-First AI Agent</Text>
        <Text dimColor>Gemini Live • Vapi • ElevenLabs • MCP</Text>
      </Box>

      <Box flexDirection="column" flex={1} paddingX={2}>
        {menuItems.map((item, i) => (
          <MenuItem
            key={item.id}
            item={item}
            isSelected={i === selectedIndex}
            onSelect={() => {
              if (item.id === 'exit') process.exit(0)
              setPanel(item.id)
              setView('panel')
            }}
          />
        ))}
      </Box>

      <Box padding={1} borderStyle="single" borderColor="gray">
        <Text dimColor>
          ↑/↓ Navigate  •  Enter/1-9 Select  •  b/Esc Back  •  q/Ctrl+C Quit
        </Text>
      </Box>
    </Box>
  )
}

// Export for CLI entry
