import React, { useState, useEffect } from 'react';
import { cn, getStatusColor, getStatusDot } from '../lib/utils';

interface VoicePanelProps {
  status: Record<string, any>;
}

export function VoicePanel({ status }: VoicePanelProps) {
  const [voiceStatus, setVoiceStatus] = useState(status.voice || {});
  const [bridgeType, setBridgeType] = useState<'gemini' | 'vapi' | 'elevenlabs' | 'voip'>('gemini');
  const [connecting, setConnecting] = useState(false);
  const [formData, setFormData] = useState({
    gemini: { guildId: '', channelId: '' },
    vapi: { guildId: '', channelId: '', assistantId: '' },
    elevenlabs: { guildId: '', channelId: '', agentId: '' },
    voip: { ariUrl: '', ariUser: '', ariPassword: '', dograhWs: '' },
  });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('/api/voice/status');
        if (res.ok) setVoiceStatus(await res.json());
      } catch {}
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleConnect = async (type: string) => {
    setConnecting(true);
    try {
      const data = formData[type as keyof typeof formData];
      const res = await fetch('/api/voice/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, ...data }),
      });
      if (res.ok) {
        setVoiceStatus({ ...voiceStatus, status: 'connecting' });
      }
    } catch (e) {
      console.error(e);
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await fetch('/api/voice/stop', { method: 'POST' });
      setVoiceStatus({ ...voiceStatus, status: 'stopped' });
    } catch (e) {
      console.error(e);
    }
  };

  const currentConfig = formData[bridgeType];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Voice Bridges</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Manage real-time voice connections
        </p>
      </div>

      {/* Bridge Type Tabs */}
      <div className="flex gap-2 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
        {[
          { id: 'gemini', label: 'Gemini Live', icon: '🔮' },
          { id: 'vapi', label: 'Vapi.ai', icon: '📞' },
          { id: 'elevenlabs', label: 'ElevenLabs', icon: '🎙️' },
          { id: 'voip', label: 'VOIP (Asterisk)', icon: '☎️' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setBridgeType(tab.id as any)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all',
              bridgeType === tab.id
                ? 'bg-white dark:bg-gray-700 shadow-sm text-purple-700 dark:text-purple-300'
                : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
            )}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Current Status */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{bridgeType.charAt(0).toUpperCase() + bridgeType.slice(1)} Live</h2>
          <div className="flex items-center gap-3">
            <span
              className={cn(
                'w-3 h-3 rounded-full',
                getStatusDot(voiceStatus.status || 'stopped')
              )}
            />
            <span className={cn('font-medium', getStatusColor(voiceStatus.status || 'stopped'))}>
              {voiceStatus.status || 'stopped'}
            </span>
          </div>
        </div>

        {/* Connection Form */}
        <div className="space-y-4 max-w-md">
          {bridgeType === 'gemini' && (
            <>
              <FormField label="Discord Guild ID" value={currentConfig.guildId} onChange={(v) => setFormData({...formData, gemini: {...currentConfig, guildId: v}})} placeholder="1234567890" />
              <FormField label="Discord Channel ID" value={currentConfig.channelId} onChange={(v) => setFormData({...formData, gemini: {...currentConfig, channelId: v}})} placeholder="1234567890" />
            </>
          )}
          {bridgeType === 'vapi' && (
            <>
              <FormField label="Discord Guild ID" value={currentConfig.guildId} onChange={(v) => setFormData({...formData, vapi: {...currentConfig, guildId: v}})} placeholder="1234567890" />
              <FormField label="Discord Channel ID" value={currentConfig.channelId} onChange={(v) => setFormData({...formData, vapi: {...currentConfig, channelId: v}})} placeholder="1234567890" />
              <FormField label="Assistant ID" value={currentConfig.assistantId} onChange={(v) => setFormData({...formData, vapi: {...currentConfig, assistantId: v}})} placeholder="asst_..." />
            </>
          )}
          {bridgeType === 'elevenlabs' && (
            <>
              <FormField label="Discord Guild ID" value={currentConfig.guildId} onChange={(v) => setFormData({...formData, elevenlabs: {...currentConfig, guildId: v}})} placeholder="1234567890" />
              <FormField label="Discord Channel ID" value={currentConfig.channelId} onChange={(v) => setFormData({...formData, elevenlabs: {...currentConfig, channelId: v}})} placeholder="1234567890" />
              <FormField label="Agent ID" value={currentConfig.agentId} onChange={(v) => setFormData({...formData, elevenlabs: {...currentConfig, agentId: v}})} placeholder="agent_..." />
            </>
          )}
          {bridgeType === 'voip' && (
            <>
              <FormField label="ARI URL" value={currentConfig.ariUrl} onChange={(v) => setFormData({...formData, voip: {...currentConfig, ariUrl: v}})} placeholder="http://localhost:8088/ari" />
              <FormField label="ARI Username" value={currentConfig.ariUser} onChange={(v) => setFormData({...formData, voip: {...currentConfig, ariUser: v}})} placeholder="sora" />
              <FormField label="ARI Password" value={currentConfig.ariPassword} onChange={(v) => setFormData({...formData, voip: {...currentConfig, ariPassword: v}})} type="password" placeholder="••••••••" />
              <FormField label="Dograh WebSocket" value={currentConfig.dograhWs} onChange={(v) => setFormData({...formData, voip: {...currentConfig, dograhWs: v}})} placeholder="ws://dograh.example.com/gemini" />
            </>
          )}

          <div className="flex gap-3 pt-4">
            <button
              onClick={() => handleConnect(bridgeType)}
              disabled={connecting || !currentConfig.guildId || !currentConfig.channelId}
              className={cn(
                'flex-1 py-3 px-4 rounded-lg font-medium transition-colors',
                'bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {connecting ? 'Connecting...' : voiceStatus.status === 'running' ? 'Connected' : 'Connect'}
            </button>
            {(voiceStatus.status === 'running' || voiceStatus.status === 'connecting') && (
              <button
                onClick={handleDisconnect}
                className="flex-1 py-3 px-4 rounded-lg font-medium text-red-600 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
              >
                Disconnect
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Active Calls */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Active Calls</h2>
        {voiceStatus.calls && voiceStatus.calls.length > 0 ? (
          <div className="space-y-3">
            {voiceStatus.calls.map((call: any) => (
              <div key={call.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center gap-4">
                  <span className={cn('w-3 h-3 rounded-full', getStatusDot(call.status))} />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">Guild: {call.guildId}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Channel: {call.channelId}</p>
                  </div>
                </div>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {call.duration ? `${Math.floor(call.duration / 60)}m ${call.duration % 60}s` : 'Connecting...'}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">No active calls</p>
        )}
      </div>

      {/* Provider Quick Toggle */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Active Providers</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ProviderBadge name="LLM Voice" provider={voiceStatus.llmProvider || 'gemini-live'} />
          <ProviderBadge name="TTS" provider={voiceStatus.ttsProvider || 'edge-tts'} />
          <ProviderBadge name="STT" provider={voiceStatus.sttProvider || 'faster-whisper'} />
        </div>
      </div>
    </div>
  );
}

function FormField({ label, value, onChange, placeholder, type = 'text' }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string; type?: string }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
      />
    </div>
  );
}

function ProviderBadge({ name, provider }: { name: string; provider: string }) {
  return (
    <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{name}</p>
      <p className="text-lg font-semibold text-gray-900 dark:text-white mt-1">{provider}</p>
    </div>
  );
}