import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
  return `${Math.floor(ms / 3600000)}h ${Math.floor((ms % 3600000) / 60000)}m`;
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'healthy':
    case 'running':
    case 'connected':
      return 'text-green-600 dark:text-green-400';
    case 'warning':
    case 'degraded':
      return 'text-yellow-600 dark:text-yellow-400';
    case 'error':
    case 'stopped':
    case 'disconnected':
      return 'text-red-600 dark:text-red-400';
    default:
      return 'text-gray-600 dark:text-gray-400';
  }
}

export function getStatusDot(status: string): string {
  switch (status) {
    case 'healthy':
    case 'running':
    case 'connected':
      return 'bg-green-500';
    case 'warning':
    case 'degraded':
      return 'bg-yellow-500';
    case 'error':
    case 'stopped':
    case 'disconnected':
      return 'bg-red-500';
    default:
      return 'bg-gray-500';
  }
}