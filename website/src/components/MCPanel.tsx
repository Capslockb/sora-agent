import React, { useState, useEffect } from 'react';
import { cn, getStatusColor, getStatusDot } from '../lib/utils';

interface MCPanelProps {
  status: Record<string, any>;
}

export function MCPanel({ status }: MCPanelProps) {
  const [mcpStatus, setMcpStatus] = useState(status.mcp || {});
  const [servers, setServers] = useState<any[]>([]);
  const [detected, setDetected] = useState<any[]>([]);
  const [wsStatus, setWsStatus] = useState({ running: false, clients: 0 });
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusRes, serversRes, detectedRes, wsRes] = await Promise.all([
          fetch('/api/mcp/status'),
          fetch('/api/mcp/servers'),
          fetch('/api/mcp/detect'),
          fetch('/api/mcp/ws/status'),
        ]);
        if (statusRes.ok) setMcpStatus(await statusRes.json());
        if (serversRes.ok) setServers(await serversRes.json());
        if (detectedRes.ok) setDetected(await detectedRes.json());
        if (wsRes.ok) setWsStatus(await wsRes.json());
      } catch {}
    };
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStartMcp = async (transport: string) => {
    setStarting(true);
    try {
      await fetch('/api/mcp/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transport, port: 3000 }),
      });
      setMcpStatus({ ...mcpStatus, status: 'starting', transport });
    } catch (e) {
      console.error(e);
    } finally {
      setStarting(false);
    }
  };

  const handleStartWs = async () => {
    setStarting(true);
    try {
      await fetch('/api/mcp/ws/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ host: '0.0.0.0', port: 3001 }),
      });
      setWsStatus({ ...wsStatus, running: true });
    } catch (e) {
      console.error(e);
    } finally {
      setStarting(false);
    }
  };

  const handleStop = async (type: 'mcp' | 'ws') => {
    try {
      if (type === 'mcp') {
        await fetch('/api/mcp/stop', { method: 'POST' });
        setMcpStatus({ ...mcpStatus, status: 'stopped' });
      } else {
        await fetch('/api/mcp/ws/stop', { method: 'POST' });
        setWsStatus({ ...wsStatus, running: false });
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">MCP Servers</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Manage Model Context Protocol servers
        </p>
      </div>

      {/* Control Panel */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* STDIO/SSE/HTTP Server */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Primary MCP Server</h2>
            <div className="flex items-center gap-3 mb-4">
              <span className={cn('w-3 h-3 rounded-full', getStatusDot(mcpStatus.status || 'stopped'))} />
              <span className={cn('font-medium', getStatusColor(mcpStatus.status || 'stopped'))}>
                {mcpStatus.status || 'stopped'}
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {mcpStatus.transport ? `(${mcpStatus.transport})` : ''}
              </span>
            </div>

            <div className="flex flex-wrap gap-3 mb-4">
              <button
                onClick={() => handleStartMcp('stdio')}
                disabled={starting || mcpStatus.status === 'running'}
                className={cn(
                  'px-4 py-2 rounded-lg font-medium transition-colors',
                  mcpStatus.transport === 'stdio' && mcpStatus.status === 'running'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50'
                )}
              >
                Start stdio
              </button>
              <button
                onClick={() => handleStartMcp('sse')}
                disabled={starting || mcpStatus.status === 'running'}
                className={cn(
                  'px-4 py-2 rounded-lg font-medium transition-colors',
                  mcpStatus.transport === 'sse' && mcpStatus.status === 'running'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50'
                )}
              >
                Start SSE
              </button>
              <button
                onClick={() => handleStartMcp('streamable-http')}
                disabled={starting || mcpStatus.status === 'running'}
                className={cn(
                  'px-4 py-2 rounded-lg font-medium transition-colors',
                  mcpStatus.transport === 'streamable-http' && mcpStatus.status === 'running'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50'
                )}
              >
                Start HTTP
              </button>
            </div>

            {(mcpStatus.status === 'running' || mcpStatus.status === 'starting') && (
              <button
                onClick={() => handleStop('mcp')}
                className="px-4 py-2 rounded-lg font-medium text-red-600 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
              >
                Stop Server
              </button>
            )}
          </div>

          {/* WebSocket Server */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">WebSocket MCP</h2>
            <div className="flex items-center gap-3 mb-4">
              <span className={cn('w-3 h-3 rounded-full', getStatusDot(wsStatus.running ? 'running' : 'stopped'))} />
              <span className={cn('font-medium', getStatusColor(wsStatus.running ? 'running' : 'stopped'))}>
                {wsStatus.running ? 'running' : 'stopped'}
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {wsStatus.clients || 0} clients
              </span>
            </div>

            {wsStatus.running ? (
              <button
                onClick={() => handleStop('ws')}
                className="px-4 py-2 rounded-lg font-medium text-red-600 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
              >
                Stop WebSocket
              </button>
            ) : (
              <button
                onClick={handleStartWs}
                disabled={starting}
                className="px-4 py-2 rounded-lg font-medium bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50"
              >
                Start WebSocket (port 3001)
              </button>
            )}

            {wsStatus.running && (
              <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg text-sm">
                <code className="text-green-600 dark:text-green-400">ws://localhost:3001/mcp</code>
                <p className="text-gray-500 dark:text-gray-400 mt-1">Connect MCP clients to this endpoint</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Configured Servers */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Configured Servers</h2>
        {servers.length > 0 ? (
          <div className="space-y-3">
            {servers.map((server) => (
              <div key={server.name} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center gap-4">
                  <span className={cn('w-3 h-3 rounded-full', getStatusDot(server.enabled ? 'running' : 'stopped'))} />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{server.name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {server.command} {server.args?.join(' ') || ''} ({server.transport})
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <input
                      type="checkbox"
                      checked={server.enabled}
                      onChange={(e) => {
                        const updated = servers.map(s => s.name === server.name ? {...s, enabled: e.target.checked} : s);
                        setServers(updated);
                        fetch('/api/mcp/servers', {
                          method: 'PUT',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ servers: updated }),
                        });
                      }}
                      className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                    />
                    Enabled
                  </label>
                  <button
                    onClick={() => {
                      const updated = servers.filter(s => s.name !== server.name);
                      setServers(updated);
                      fetch('/api/mcp/servers', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ servers: updated }),
                      });
                    }}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">No servers configured</p>
        )}

        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button className="w-full py-2 px-4 rounded-lg font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
            + Add MCP Server
          </button>
        </div>
      </div>

      {/* Detected Servers */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Detected on System</h2>
        {detected.length > 0 ? (
          <div className="space-y-3">
            {detected.map((d, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full bg-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {d.type === 'stdio' ? 'STDIO Process' : `Port ${d.port}`}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {d.process} (PID: {d.pid}){d.cmdline && ` — ${d.cmdline}`}
                    </p>
                  </div>
                </div>
                <button className="text-sm text-purple-600 hover:text-purple-800">
                  Auto-configure
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">No MCP servers detected</p>
        )}
      </div>
    </div>
  );
}