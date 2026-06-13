import React from 'react';
import { cn, getStatusColor, getStatusDot } from '../lib/utils';

interface StatusBarProps {
  status: Record<string, any>;
}

export function StatusBar({ status }: StatusBarProps) {
  const voiceStatus = status.voice || {};
  const mcpStatus = status.mcp || {};
  const systemStatus = status.system || {};

  return (
    <div className="flex items-center gap-4">
      {/* Voice Status */}
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-700">
        <span
          className={cn(
            'w-2 h-2 rounded-full',
            getStatusDot(voiceStatus.status || 'unknown')
          )}
        />
        <span className={cn('text-xs font-medium', getStatusColor(voiceStatus.status || 'unknown'))}>
          Voice: {voiceStatus.status || 'unknown'}
        </span>
      </div>

      {/* MCP Status */}
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-700">
        <span
          className={cn(
            'w-2 h-2 rounded-full',
            getStatusDot(mcpStatus.status || 'unknown')
          )}
        />
        <span className={cn('text-xs font-medium', getStatusColor(mcpStatus.status || 'unknown'))}>
          MCP: {mcpStatus.status || 'unknown'}
        </span>
      </div>

      {/* System Status */}
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-700">
        <span
          className={cn(
            'w-2 h-2 rounded-full',
            getStatusDot(systemStatus.status || 'unknown')
          )}
        />
        <span className={cn('text-xs font-medium', getStatusColor(systemStatus.status || 'unknown'))}>
          {systemStatus.status || 'unknown'}
        </span>
      </div>
    </div>
  );
}