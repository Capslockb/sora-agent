import React, { useState, useEffect } from 'react';
import { cn, getStatusColor, getStatusDot } from '../lib/utils';

const PROVIDERS = {
  llm_voice: [
    { id: 'gemini-live', name: 'Gemini Live', description: 'Google multimodal live API', env: ['GEMINI_API_KEY', 'GOOGLE_API_KEY'] },
    { id: 'vapi', name: 'Vapi.ai', description: 'Voice AI platform', env: ['VAPI_API_KEY', 'VAPI_PRIVATE_KEY'] },
    { id: 'elevenlabs', name: 'ElevenLabs', description: 'Conversational AI', env: ['ELEVENLABS_API_KEY', 'ELEVENLABS_AGENT_ID'] },
  ],
  tts: [
    { id: 'edge-tts', name: 'Edge TTS', description: 'Microsoft neural TTS (free)', env: [] },
    { id: 'openai-tts', name: 'OpenAI TTS', description: 'OpenAI tts-1/tts-1-hd', env: ['OPENAI_API_KEY'] },
    { id: 'elevenlabs-tts', name: 'ElevenLabs TTS', description: 'Voice cloning TTS', env: ['ELEVENLABS_API_KEY'] },
    { id: 'gemini-tts', name: 'Gemini TTS', description: 'Google Gemini TTS', env: ['GEMINI_API_KEY'] },
    { id: 'minimax-tts', name: 'MiniMax TTS', description: 'Chinese-optimized', env: ['MINIMAX_API_KEY'] },
    { id: 'mistral-tts', name: 'Mistral TTS', description: 'European-optimized', env: ['MISTRAL_API_KEY'] },
  ],
  stt: [
    { id: 'faster-whisper', name: 'Faster Whisper', description: 'Local Whisper (CPU/GPU)', env: [] },
    { id: 'openai-whisper', name: 'OpenAI Whisper', description: 'Hosted Whisper API', env: ['OPENAI_API_KEY'] },
    { id: 'gemini-stt', name: 'Gemini STT', description: 'Google Gemini STT', env: ['GEMINI_API_KEY'] },
  ],
};

const CATEGORY_LABELS = {
  llm_voice: 'LLM Voice Bridges',
  tts: 'Text-to-Speech',
  stt: 'Speech-to-Text',
};

interface ProviderPanelProps {
  status: Record<string, any>;
}

export function ProviderPanel({ status }: ProviderPanelProps) {
  const [currentProviders, setCurrentProviders] = useState({
    llm_voice: status.voice?.llmProvider || 'gemini-live',
    tts: status.voice?.ttsProvider || 'edge-tts',
    stt: status.voice?.sttProvider || 'faster-whisper',
  });
  const [envVars, setEnvVars] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    // Load current env vars
    fetch('/api/config/env')
      .then(r => r.ok ? r.json() : {})
      .then(data => setEnvVars(data))
      .catch(() => {});
  }, []);

  const handleSelect = (category: string, providerId: string) => {
    setCurrentProviders(prev => ({ ...prev, [category]: providerId }));
    // Save to backend
    fetch('/api/providers/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, provider: providerId }),
    });
  };

  const handleSaveEnv = (varName: string, value: string) => {
    setSaving(varName);
    const newVars = { ...envVars, [varName]: value };
    setEnvVars(newVars);
    fetch('/api/config/env', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newVars),
    }).finally(() => setSaving(null));
  };

  const isEnvSet = (varName: string) => !!envVars[varName];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Voice Providers</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Configure TTS, STT, and LLM Voice providers
        </p>
      </div>

      {Object.entries(PROVIDERS).map(([category, providers]) => (
        <div key={category} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {CATEGORY_LABELS[category as keyof typeof CATEGORY_LABELS]}
          </h2>

          <div className="space-y-3">
            {providers.map((provider) => {
              const isActive = currentProviders[category as keyof typeof currentProviders] === provider.id;
              const missingEnv = provider.env.filter(v => !isEnvSet(v));
              const hasMissingEnv = missingEnv.length > 0;

              return (
                <div
                  key={provider.id}
                  className={cn(
                    'flex items-center justify-between p-4 rounded-lg border transition-colors',
                    isActive
                      ? 'border-purple-300 dark:border-purple-700 bg-purple-50 dark:bg-purple-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  )}
                >
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <button
                      onClick={() => handleSelect(category, provider.id)}
                      className={cn(
                        'w-5 h-5 rounded border-2 flex-shrink-0 transition-colors',
                        isActive
                          ? 'border-purple-500 bg-purple-500'
                          : 'border-gray-300 dark:border-gray-600 hover:border-purple-500'
                      )}
                      aria-label={isActive ? 'Active' : 'Select'}
                    >
                      {isActive && (
                        <svg className="w-3 h-3 text-white mx-auto my-0.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-gray-900 dark:text-white truncate">{provider.name}</p>
                        {isActive && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">
                            Active
                          </span>
                        )}
                        {hasMissingEnv && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300">
                            Needs config
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{provider.description}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 ml-4">
                    {provider.env.length > 0 && (
                      <div className="flex items-center gap-2">
                        {provider.env.map((envVar) => (
                          <EnvVarBadge
                            key={envVar}
                            name={envVar}
                            isSet={isEnvSet(envVar)}
                            onSet={(val) => handleSaveEnv(envVar, val)}
                            saving={saving === envVar}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {/* Environment Variables Manager */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Environment Variables</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Manage API keys and secrets. Values are stored securely in ~/.sora/.env
        </p>

        <div className="space-y-3 max-w-2xl">
          {[
            'GEMINI_API_KEY', 'GOOGLE_API_KEY', 'VAPI_API_KEY', 'VAPI_PRIVATE_KEY',
            'ELEVENLABS_API_KEY', 'ELEVENLABS_AGENT_ID', 'OPENAI_API_KEY',
            'MINIMAX_API_KEY', 'MINIMAX_GROUP_ID', 'MISTRAL_API_KEY',
            'DISCORD_TOKEN', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID',
            'GITHUB_TOKEN', 'HONCHO_API_KEY',
          ].map((varName) => (
            <EnvVarRow
              key={varName}
              name={varName}
              value={envVars[varName] || ''}
              onSave={(val) => handleSaveEnv(varName, val)}
              saving={saving === varName}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function EnvVarBadge({ name, isSet, onSet, saving }: { name: string; isSet: boolean; onSet: (val: string) => void; saving: boolean }) {
  const [showInput, setShowInput] = useState(false);
  const [inputValue, setInputValue] = useState('');

  const handleSave = () => {
    if (inputValue.trim()) {
      onSet(inputValue.trim());
      setShowInput(false);
      setInputValue('');
    }
  };

  if (isSet) {
    return (
      <span className="flex items-center gap-1.5 px-2 py-1 rounded bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs">
        <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
        {name}
      </span>
    );
  }

  if (showInput) {
    return (
      <div className="flex items-center gap-2">
        <input
          type="password"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSave()}
          onBlur={handleSave}
          placeholder={name}
          autoFocus
          className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 w-48"
        />
        <button onClick={handleSave} disabled={saving || !inputValue.trim()} className="text-xs text-purple-600 hover:text-purple-800 disabled:opacity-50">
          Save
        </button>
        <button onClick={() => { setShowInput(false); setInputValue(''); }} className="text-xs text-gray-500 hover:text-gray-700">
          Cancel
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={() => setShowInput(true)}
      className="flex items-center gap-1.5 px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 text-xs hover:bg-gray-200 dark:hover:bg-gray-600"
    >
      <span className="w-1.5 h-1.5 rounded-full border border-gray-300 dark:border-gray-600" />
      {name}
    </button>
  );
}

function EnvVarRow({ name, value, onSave, saving }: { name: string; value: string; onSave: (val: string) => void; saving: boolean }) {
  const [editing, setEditing] = useState(false);
  const [inputValue, setInputValue] = useState(value);

  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <code className="text-sm font-mono text-gray-700 dark:text-gray-300 w-48 flex-shrink-0">{name}</code>
      {editing ? (
        <div className="flex-1 flex gap-2">
          <input
            type="password"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onSave(inputValue)}
            onBlur={() => { onSave(inputValue); setEditing(false); }}
            autoFocus
            className="flex-1 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-600"
          />
          <button onClick={() => { onSave(inputValue); setEditing(false); }} disabled={saving} className="px-3 py-1 text-sm text-purple-600 hover:text-purple-800 disabled:opacity-50">
            Save
          </button>
          <button onClick={() => { setInputValue(value); setEditing(false); }} className="px-3 py-1 text-sm text-gray-500 hover:text-gray-700">
            Cancel
          </button>
        </div>
      ) : (
        <div className="flex-1 flex items-center gap-3">
          <span className={cn(
            'px-2 py-1 text-sm rounded',
            value ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-gray-200 dark:bg-gray-600 text-gray-500 dark:text-gray-400'
          )}>
            {value ? '•••••••• (set)' : 'Not set'}
          </span>
          <button onClick={() => { setInputValue(value); setEditing(true); }} className="text-sm text-purple-600 hover:text-purple-800">
            {value ? 'Change' : 'Set'}
          </button>
        </div>
      )}
    </div>
  );
}