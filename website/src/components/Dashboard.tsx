import React, { useState, useEffect } from 'react';
import { cn, formatDuration, formatBytes, getStatusColor, getStatusDot } from '../lib/utils';

interface DashboardProps {
  status: Record<string, any>;
}

const stats = [
  { label: 'Uptime', key: 'uptime', format: formatDuration },
  { label: 'Memory', key: 'memory', format: formatBytes },
  { label: 'CPU', key: 'cpu', format: (v: number) => `${v}%` },
  { label: 'Active Calls', key: 'calls', format: (v: number) => String(v) },
];

export function Dashboard({ status }: DashboardProps) {
  const [systemStats, setSystemStats] = useState<Record<string, any>>({});
  const [recentCalls, setRecentCalls] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, callsRes] = await Promise.all([
          fetch('/api/dashboard/stats'),
          fetch('/api/dashboard/calls'),
        ]);
        if (statsRes.ok) setSystemStats(await statsRes.json());
        if (callsRes.ok) setRecentCalls(await callsRes.json());
      } catch {
        // Ignore
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const voice = status.voice || {};
  const mcp = status.mcp || {};
  const system = status.system || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Overview of your S0RA Agent system
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatusCard
          title="Voice Bridge"
          status={voice.status || 'unknown'}
          details={[
            { label: 'Type', value: voice.type || '—' },
            { label: 'Model', value: voice.model || '—' },
            { label: 'Active Calls', value: voice.activeCalls || 0 },
          ]}
        />
        <StatusCard
          title="MCP Server"
          status={mcp.status || 'unknown'}
          details={[
            { label: 'Transport', value: mcp.transport || '—' },
            { label: 'Port', value: mcp.port || '—' },
            { label: 'Connected Clients', value: mcp.clients || 0 },
          ]}
        />
        <StatusCard
          title="VOIP Bridge"
          status={status.voip?.status || 'stopped'}
          details={[
            { label: 'ARI Connected', value: status.voip?.ari ? 'Yes' : 'No' },
            { label: 'Base Port', value: status.voip?.port || '—' },
            { label: 'Active Calls', value: status.voip?.calls || 0 },
          ]}
        />
        <StatusCard
          title="System"
          status={system.status || 'unknown'}
          details={[
            { label: 'Platform', value: system.platform || '—' },
            { label: 'Python', value: system.python || '—' },
            { label: 'Uptime', value: systemStats.uptime ? formatDuration(systemStats.uptime) : '—' },
          ]}
        />
      </div>

      {/* System Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <StatCard
            key={stat.key}
            label={stat.label}
            value={stat.format(systemStats[stat.key] || 0)}
            loading={loading}
          />
        ))}
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Voice Activity */}
        <Card title="Recent Voice Activity" subtitle={voice.status}>
          {recentCalls.length > 0 ? (
            <div className="space-y-3">
              {recentCalls.slice(0, 5).map((call: any) => (
                <div key={call.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span
                      className={cn(
                        'w-2 h-2 rounded-full',
                        getStatusDot(call.status)
                      )}
                    />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {call.type || 'Call'}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {call.duration ? formatDuration(call.duration) : 'Connecting...'}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {call.timestamp ? new Date(call.timestamp).toLocaleTimeString() : '—'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              {loading ? (
                <div className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Loading...</span>
                </div>
              ) : (
                'No recent voice activity'
              )}
            </div>
          )}
        </Card>

        {/* Quick Actions */}
        <Card title="Quick Actions">
          <div className="grid grid-cols-2 gap-3">
            <ActionButton
              label="Start Voice"
              description="Launch Gemini Live"
              icon="Mic"
              onClick={() => window.location.href = '/voice'}
            />
            <ActionButton
              label="Start MCP"
              description="Launch MCP server"
              icon="Cpu"
              onClick={() => window.location.href = '/mcp'}
            />
            <ActionButton
              label="Providers"
              description="Configure TTS/STT"
              icon="PlugZap"
              onClick={() => window.location.href = '/providers'}
            />
            <ActionButton
              label="Settings"
              description="System settings"
              icon="Settings"
              onClick={() => window.location.href = '/settings'}
            />
          </div>
        </Card>
      </div>
    </div>
  );
}

function StatusCard({ title, status, details }: { title: string; status: string; details: { label: string; value: string | number }[] }) {
  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className={cn('w-3 h-3 rounded-full', getStatusDot(status))} />
            <span className={cn('text-lg font-semibold', getStatusColor(status))}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
          </div>
        </div>
      </div>
      <div className="mt-4 space-y-2">
        {details.map((d, i) => (
          <div key={i} className="flex justify-between text-sm">
            <span className="text-gray-500 dark:text-gray-400">{d.label}</span>
            <span className="font-medium text-gray-900 dark:text-white">{d.value}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

function StatCard({ label, value, loading }: { label: string; value: string; loading: boolean }) {
  return (
    <Card>
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</p>
      <p className={cn('mt-2 text-3xl font-bold text-gray-900 dark:text-white', loading && 'animate-pulse')}>
        {loading ? '—' : value}
      </p>
    </Card>
  );
}

function Card({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
        {subtitle && (
          <span className="text-xs px-2 py-1 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">
            {subtitle}
          </span>
        )}
      </div>
      {children}
    </div>
  );
}

function ActionButton({ label, description, icon, onClick }: { label: string; description: string; icon: string; onClick: () => void }) {
  const icons: Record<string, React.ReactNode> = {
    Mic: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>,
    Cpu: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" /></svg>,
    PlugZap: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>,
    Settings: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
  };

  return (
    <button
      onClick={onClick}
      className="p-4 text-left rounded-lg border border-gray-200 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-700 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors"
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-600 dark:text-purple-400">
          {icons[icon]}
        </div>
        <div>
          <p className="font-medium text-gray-900 dark:text-white">{label}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
        </div>
      </div>
    </button>
  );
}