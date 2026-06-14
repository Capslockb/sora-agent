import express from 'express';
import { readFileSync, existsSync } from 'fs';
import { resolve } from 'path';
import os from 'os';

const app = express();
const PORT = 3001;

// CORS
app.use((_req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  if (_req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

function loadSoraEnv() {
  const path = resolve(os.homedir(), '.sora', '.env');
  const vars = {};
  if (existsSync(path)) {
    try {
      const content = readFileSync(path, 'utf8');
      for (const line of content.split('\n')) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        const eq = trimmed.indexOf('=');
        if (eq > 0) {
          vars[trimmed.substring(0, eq).trim()] = trimmed.substring(eq + 1).trim();
        }
      }
    } catch (e) { console.error('env read error:', e.message); }
  }
  // Merge process.env
  for (const [k, v] of Object.entries(process.env)) {
    if (v && !vars[k]) vars[k] = v;
  }
  return vars;
}

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.get('/api/config', (_req, res) => {
  const env = loadSoraEnv();
  const providers = {
    'elevenlabs-widget': {
      enabled: !!(env.ELEVENLABS_API_KEY && env.ELEVENLABS_AGENT_ID),
      agentId: env.ELEVENLABS_AGENT_ID ? env.ELEVENLABS_AGENT_ID.substring(0, 12) + '...' : null,
    },
    'elevenlabs-sdk': {
      enabled: !!(env.ELEVENLABS_API_KEY && env.ELEVENLABS_AGENT_ID),
    },
    'vapi': { enabled: !!(env.VAPI_API_KEY) },
    'openai': { enabled: !!(env.OPENAI_API_KEY) },
    'xai': { enabled: !!(env.XAI_API_KEY) },
    'ultravox': { enabled: !!(env.ULTRAVOX_API_KEY) },
    'retell': { enabled: !!(env.RETELL_API_KEY) },
    'gemini': { enabled: !!(env.GEMINI_API_KEY || env.GOOGLE_API_KEY) },
  };
  const configured = Object.entries(providers).filter(([,p]) => p.enabled).map(([k]) => k);
  res.json({ providers, configured, source: '~/.sora/.env' });
});

app.listen(PORT, () => {
  console.log(`[Sora Config API] http://127.0.0.1:${PORT}`);
  console.log(`[Sora Config API] Reading from ~/.sora/.env`);
});

setInterval(() => {}, 10000);
