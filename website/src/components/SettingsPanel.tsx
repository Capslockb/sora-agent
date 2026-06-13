import React, { useState, useEffect } from 'react';
import { cn } from '../lib/utils';

interface SettingsPanelProps {
  status: Record<string, any>;
}

export function SettingsPanel({ status }: SettingsPanelProps) {
  const [config, setConfig] = useState<any>({});
  const [saving, setSaving] = useState(false);
  const [tabs, setTabs] = useState<'general' | 'voice' | 'mcp' | 'network' | 'advanced'>('general');

  useEffect(() => {
    fetch('/api/config')
      .then(r => r.ok ? r.json() : {})
      .then(data => setConfig(data))
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await fetch('/api/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const updateConfig = (path: string, value: any) => {
    const keys = path.split('.');
    const newConfig = JSON.parse(JSON.stringify(config));
    let obj = newConfig;
    for (let i = 0; i < keys.length - 1; i++) {
      obj[keys[i]] = obj[keys[i]] || {};
      obj = obj[keys[i]];
    }
    obj[keys[keys.length - 1]] = value;
    setConfig(newConfig);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Configure S0RA Agent behavior
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
        {[
          { id: 'general', label: 'General' },
          { id: 'voice', label: 'Voice' },
          { id: 'mcp', label: 'MCP' },
          { id: 'network', label: 'Network' },
          { id: 'advanced', label: 'Advanced' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setTabs(tab.id as any)}
            className={cn(
              'px-4 py-2 rounded-md text-sm font-medium transition-all',
              tabs === tab.id
                ? 'bg-white dark:bg-gray-700 shadow-sm text-purple-700 dark:text-purple-300'
                : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        {tabs === 'general' && <GeneralSettings config={config} onChange={updateConfig} />}
        {tabs === 'voice' && <VoiceSettings config={config} onChange={updateConfig} />}
        {tabs === 'mcp' && <MCPSettings config={config} onChange={updateConfig} />}
        {tabs === 'network' && <NetworkSettings config={config} onChange={updateConfig} />}
        {tabs === 'advanced' && <AdvancedSettings config={config} onChange={updateConfig} />}
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-3 rounded-lg font-medium bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 transition-colors"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
}

// --- Tab Components ---

function GeneralSettings({ config, onChange }: { config: any; onChange: (path: string, value: any) => void }) {
  return (
    <div className="space-y-6 max-w-2xl">
      <SettingGroup title="Profile" description="Active S0RA profile">
        <SelectSetting
          label="Profile"
          path="profile"
          value={config.profile || 'default'}
          options={[
            { value: 'default', label: 'Default' },
            { value: 'work', label: 'Work' },
            { value: 'personal', label: 'Personal' },
          ]}
          onChange={onChange}
        />
      </SettingGroup>

      <SettingGroup title="Interface" description="UI preferences">
        <SelectSetting
          label="Default Interface"
          path="display.interface"
          value={config.display?.interface || 'cli'}
          options={[
            { value: 'cli', label: 'CLI (classic)' },
            { value: 'tui', label: 'TUI (Ink/React)' },
            { value: 'web', label: 'Web Dashboard' },
          ]}
          onChange={onChange}
        />
        <SelectSetting
          label="Theme"
          path="display.theme"
          value={config.display?.theme || 'system'}
          options={[
            { value: 'system', label: 'System' },
            { value: 'light', label: 'Light' },
            { value: 'dark', label: 'Dark' },
          ]}
          onChange={onChange}
        />
        <ToggleSetting
          label="Show ASCII Art"
          path="display.ascii_art"
          value={config.display?.ascii_art ?? true}
          onChange={onChange}
        />
        <ToggleSetting
          label="Animated Spinners"
          path="display.spinners"
          value={config.display?.spinners ?? true}
          onChange={onChange}
        />
      </SettingGroup>

      <SettingGroup title="Behavior" description="Core behavior settings">
        <ToggleSetting
          label="Auto-load .env"
          path="core.auto_load_env"
          value={config.core?.auto_load_env ?? true}
          onChange={onChange}
        />
        <ToggleSetting
          label="Redact Secrets in Logs"
          path="security.redact_secrets"
          value={config.security?.redact_secrets ?? true}
          onChange={onChange}
        />
        <ToggleSetting
          label="Telemetry"
          path="telemetry.enabled"
          value={config.telemetry?.enabled ?? false}
          onChange={onChange}
        />
        <NumberSetting
          label="Default Timeout (seconds)"
          path="core.default_timeout"
          value={config.core?.default_timeout || 30}
          min={5}
          max={300}
          onChange={onChange}
        />
      </SettingGroup>
    </div>
  );
}

function VoiceSettings({ config, onChange }: { config: any; onChange: (path: string, value: any) => void }) {
  return (
    <div className="space-y-6 max-w-2xl">
      <SettingGroup title="Default Providers" description="Primary voice providers">
        <SelectSetting
          label="LLM Voice"
          path="voice.provider"
          value={config.voice?.provider || 'gemini-live'}
          options={[
            { value: 'gemini-live', label: 'Gemini Live' },
            { value: 'vapi', label: 'Vapi.ai' },
            { value: 'elevenlabs', label: 'ElevenLabs' },
          ]}
          onChange={onChange}
        />
        <SelectSetting
          label="TTS Provider"
          path="voice.tts.provider"
          value={config.voice?.tts?.provider || 'edge-tts'}
          options={[
            { value: 'edge-tts', label: 'Edge TTS (free)' },
            { value: 'openai-tts', label: 'OpenAI TTS' },
            { value: 'elevenlabs-tts', label: 'ElevenLabs TTS' },
            { value: 'gemini-tts', label: 'Gemini TTS' },
            { value: 'minimax-tts', label: 'MiniMax TTS' },
            { value: 'mistral-tts', label: 'Mistral TTS' },
          ]}
          onChange={onChange}
        />
        <SelectSetting
          label="STT Provider"
          path="voice.stt.provider"
          value={config.voice?.stt?.provider || 'faster-whisper'}
          options={[
            { value: 'faster-whisper', label: 'Faster Whisper (local)' },
            { value: 'openai-whisper', label: 'OpenAI Whisper API' },
            { value: 'gemini-stt', label: 'Gemini STT' },
          ]}
          onChange={onChange}
        />
      </SettingGroup>

      <SettingGroup title="Gemini Live" description="Gemini Live API settings">
        <SelectSetting
          label="Model"
          path="voice.gemini_live.model"
          value={config.voice?.gemini_live?.model || 'gemini-2.0-flash-exp'}
          options={[
            { value: 'gemini-2.0-flash-exp', label: 'Gemini 2.0 Flash Exp' },
            { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
            { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
          ]}
          onChange={onChange}
        />
        <SelectSetting
          label="Voice"
          path="voice.gemini_live.voice"
          value={config.voice?.gemini_live?.voice || 'Puck'}
          options={[
            { value: 'Puck', label: 'Puck' },
            { value: 'Charon', label: 'Charon' },
            { value: 'Kore', label: 'Kore' },
            { value: 'Fenrir', label: 'Fenrir' },
            { value: 'Aoede', label: 'Aoede' },
          ]}
          onChange={onChange}
        />
        <NumberSetting
          label="Temperature"
          path="voice.gemini_live.temperature"
          value={config.voice?.gemini_live?.temperature || 0.7}
          min={0}
          max={2}
          step={0.1}
          onChange={onChange}
        />
      </SettingGroup>

      <SettingGroup title="Wake Word" description="OpenWakeWord 'Hey Sora'">
        <ToggleSetting
          label="Enable Wake Word"
          path="voice.wake_word.enabled"
          value={config.voice?.wake_word?.enabled ?? false}
          onChange={onChange}
        />
        <TextSetting
          label="Wake Word Model"
          path="voice.wake_word.model"
          value={config.voice?.wake_word?.model || 'hey_sora'}
          onChange={onChange}
        />
        <NumberSetting
          label="Sensitivity"
          path="voice.wake_word.sensitivity"
          value={config.voice?.wake_word?.sensitivity || 0.5}
          min={0}
          max={1}
          step={0.05}
          onChange={onChange}
        />
      </SettingGroup>
    </div>
  );
}

function MCPSettings({ config, onChange }: { config: any; onChange: (path: string, value: any) => void }) {
  return (
    <div className="space-y-6 max-w-2xl">
      <SettingGroup title="MCP Server" description="Primary MCP server settings">
        <ToggleSetting
          label="Auto-start MCP Server"
          path="mcp.auto_start"
          value={config.mcp?.auto_start ?? false}
          onChange={onChange}
        />
        <SelectSetting
          label="Default Transport"
          path="mcp.default_transport"
          value={config.mcp?.default_transport || 'stdio'}
          options={[
            { value: 'stdio', label: 'STDIO' },
            { value: 'sse', label: 'SSE' },
            { value: 'streamable-http', label: 'Streamable HTTP' },
          ]}
          onChange={onChange}
        />
        <NumberSetting
          label="Default Port"
          path="mcp.default_port"
          value={config.mcp?.default_port || 3000}
          min={1024}
          max={65535}
          onChange={onChange}
        />
      </SettingGroup>

      <SettingGroup title="WebSocket MCP" description="Real-time WebSocket server">
        <ToggleSetting
          label="Enable WebSocket MCP"
          path="mcp.ws.enabled"
          value={config.mcp?.ws?.enabled ?? false}
          onChange={onChange}
        />
        <NumberSetting
          label="WebSocket Port"
          path="mcp.ws.port"
          value={config.mcp?.ws?.port || 3001}
          min={1024}
          max={65535}
          onChange={onChange}
        />
        <TextSetting
          label="WebSocket Host"
          path="mcp.ws.host"
          value={config.mcp?.ws?.host || '0.0.0.0'}
          onChange={onChange}
        />
      </SettingGroup>

      <SettingGroup title="Auto-Detection" description="Automatically discover MCP servers">
        <ToggleSetting
          label="Scan Ports on Startup"
          path="mcp.detect.scan_ports"
          value={config.mcp?.detect?.scan_ports ?? true}
          onChange={onChange}
        />
        <TextSetting
          label="Port Range"
          path="mcp.detect.port_range"
          value={config.mcp?.detect?.port_range || '3000-3010'}
          onChange={onChange}
        />
      </SettingGroup>
    </div>
  );
}

function NetworkSettings({ config, onChange }: { config: any; onChange: (path: string, value: any) => void }) {
  return (
    <div className="space-y-6 max-w-2xl">
      <SettingGroup title="HTTP API" description="REST API server settings">
        <TextSetting
          label="Bind Host"
          path="network.http.host"
          value={config.network?.http?.host || '0.0.0.0'}
          onChange={onChange}
        />
        <NumberSetting
          label="Port"
          path="network.http.port"
          value={config.network?.http?.port || 8080}
          min={1024}
          max={65535}
          onChange={onChange}
        />
        <ToggleSetting
          label="Enable CORS"
          path="network.http.cors"
          value={config.network?.http?.cors ?? true}
          onChange={onChange}
        />
      </SettingGroup>

      <SettingGroup title="IP Version" description="Network stack preference">
        <ToggleSetting
          label="Force IPv4"
          path="network.force_ipv4"
          value={config.network?.force_ipv4 ?? false}
          onChange={onChange}
        />
        <ToggleSetting
          label="Prefer IPv6"
          path="network.prefer_ipv6"
          value={config.network?.prefer_ipv6 ?? true}
          onChange={onChange}
        />
      </SettingGroup>

      <SettingGroup title="Proxy" description="Outbound proxy settings">
        <TextSetting
          label="HTTP Proxy"
          path="network.proxy.http"
          value={config.network?.proxy?.http || ''}
          placeholder="http://proxy:8080"
          onChange={onChange}
        />
        <TextSetting
          label="HTTPS Proxy"
          path="network.proxy.https"
          value={config.network?.proxy?.https || ''}
          placeholder="http://proxy:8080"
          onChange={onChange}
        />
        <TextSetting
          label="No Proxy"
          path="network.proxy.no_proxy"
          value={config.network?.proxy?.no_proxy || 'localhost,127.0.0.1'}
          onChange={onChange}
        />
      </SettingGroup>
    </div>
  );
}

function AdvancedSettings({ config, onChange }: { config: any; onChange: (path: string, value: any) => void }) {
  return (
    <div className="space-y-6 max-w-2xl">
      <SettingGroup title="Logging" description="Log configuration">
        <SelectSetting
          label="Log Level"
          path="logging.level"
          value={config.logging?.level || 'INFO'}
          options={[
            { value: 'DEBUG', label: 'DEBUG' },
            { value: 'INFO', label: 'INFO' },
            { value: 'WARNING', label: 'WARNING' },
            { value: 'ERROR', label: 'ERROR' },
          ]}
          onChange={onChange}
        />
        <ToggleSetting
          label="JSON Format"
          path="logging.json"
          value={config.logging?.json ?? false}
          onChange={onChange}
        />
        <TextSetting
          label="Log File"
          path="logging.file"
          value={config.logging?.file || '~/.sora/logs/sora.log'}
          onChange={onChange}
        />
      </SettingGroup>

      <SettingGroup title="Performance" description="Performance tuning">
        <NumberSetting
          label="Max Concurrent Tasks"
          path="performance.max_concurrent"
          value={config.performance?.max_concurrent || 10}
          min={1}
          max={50}
          onChange={onChange}
        />
        <NumberSetting
          label="Cache TTL (seconds)"
          path="performance.cache_ttl"
          value={config.performance?.cache_ttl || 3600}
          min={60}
          max={86400}
          onChange={onChange}
        />
        <ToggleSetting
          label="Enable Response Caching"
          path="performance.cache_enabled"
          value={config.performance?.cache_enabled ?? true}
          onChange={onChange}
        />
      </SettingGroup>

      <SettingGroup title="Danger Zone" description="⚠️ Advanced options">
        <div className="border-l-4 border-red-500 pl-4">
          <p className="text-sm text-red-600 dark:text-red-400 mb-4">
            These settings can break your installation. Only change if you know what you're doing.
          </p>
          <ToggleSetting
            label="Disable All Safety Checks"
            path="advanced.disable_safety"
            value={config.advanced?.disable_safety ?? false}
            onChange={onChange}
          />
          <ToggleSetting
            label="Allow Unverified Plugins"
            path="advanced.allow_unverified_plugins"
            value={config.advanced?.allow_unverified_plugins ?? false}
            onChange={onChange}
          />
        </div>
      </SettingGroup>
    </div>
  );
}

// --- Setting Components ---

function SettingGroup({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-semibold text-gray-900 dark:text-white">{title}</h3>
        {description && <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>}
      </div>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

function ToggleSetting({ label, path, value, onChange }: { label: string; path: string; value: boolean; onChange: (path: string, value: any) => void }) {
  return (
    <div className="flex items-center justify-between">
      <label className="text-sm text-gray-700 dark:text-gray-300">{label}</label>
      <button
        onClick={() => onChange(path, !value)}
        className={cn(
          'relative w-11 h-6 rounded-full transition-colors',
          value ? 'bg-purple-600' : 'bg-gray-300 dark:bg-gray-600'
        )}
        role="switch"
        aria-checked={value}
      >
        <span
          className={cn(
            'absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-md transition-transform',
            value ? 'translate-x-5' : 'translate-x-0'
          )}
        />
      </button>
    </div>
  );
}

function SelectSetting({ label, path, value, options, onChange }: { label: string; path: string; value: string; options: { value: string; label: string }[]; onChange: (path: string, value: any) => void }) {
  return (
    <div>
      <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(path, e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  );
}

function TextSetting({ label, path, value, placeholder, onChange }: { label: string; path: string; value: string; placeholder?: string; onChange: (path: string, value: any) => void }) {
  return (
    <div>
      <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(path, e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
      />
    </div>
  );
}

function NumberSetting({ label, path, value, min, max, step = 1, onChange }: { label: string; path: string; value: number; min: number; max: number; step?: number; onChange: (path: string, value: any) => void }) {
  return (
    <div>
      <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(path, parseFloat(e.target.value) || 0)}
        min={min}
        max={max}
        step={step}
        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
      />
    </div>
  );
}