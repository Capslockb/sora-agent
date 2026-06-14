import express from 'express';
import { readFileSync, existsSync } from 'fs';
import { resolve } from 'path';
import os from 'os';

const app = express();
const PORT = 3001;

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
    const content = readFileSync(path, 'utf8');
    for (const line of content.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eq = trimmed.indexOf('=');
      if (eq > 0) vars[trimmed.substring(0, eq).trim()] = trimmed.substring(eq + 1).trim();
    }
  }
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
  const providers = {};
  const checks = [
    ['elevenlabs-widget', () => !!(env.ELEVENLABS_API_KEY && env.ELEVENLABS_AGENT_ID)],
    ['elevenlabs-sdk', () => !!(env.ELEVENLABS_API_KEY && env.ELEVENLABS_AGENT_ID)],
    ['vapi', () => !!(env.VAPI_API_KEY)],
    ['openai', () => !!(env.OPENAI_API_KEY)],
    ['xai', () => !!(env.XAI_API_KEY)],
    ['ultravox', () => !!(env.ULTRAVOX_API_KEY)],
    ['retell', () => !!(env.RETELL_API_KEY)],
    ['gemini', () => !!(env.GEMINI_API_KEY || env.GOOGLE_API_KEY)],
  ];
  for (const [key, fn] of checks) {
    providers[key] = { enabled: fn() };
  }
  const configured = checks.filter(([,fn]) => fn()).map(([k]) => k);
  res.json({ providers, configured, source: '~/.sora/.env' });
});

app.listen(PORT, () => {
  console.log('[Sora Config API] http://localhost:' + PORT);
});
