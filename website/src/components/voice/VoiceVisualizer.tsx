import { useRef, useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface VoiceVisualizerProps {
  className?: string;
  width?: number;
  height?: number;
  barCount?: number;
  color?: string;
  responsive?: boolean;
  frequencyData: Uint8Array;
  timeDomainData?: Uint8Array;
  isActive?: boolean;
  isSpeaking?: boolean;
}

export function VoiceVisualizer({
  className,
  width = 400,
  height = 120,
  barCount = 64,
  responsive = true,
  frequencyData,
  isActive = false,
  isSpeaking = false,
}: VoiceVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const [internalActive, setInternalActive] = useState(false);
  const smoothDataRef = useRef<number[]>(new Array(barCount).fill(0));

  const active = isActive || internalActive;

  const smoothData = useCallback((newData: number[], smoothFactor = 0.3) => {
    return newData.map((value, i) => {
      const current = smoothDataRef.current[i] || 0;
      return current + (value - current) * smoothFactor;
    });
  }, []);

  const sampleFrequencyData = useCallback(
    (data: Uint8Array) => {
      if (!data || data.length === 0) return [];
      const result: number[] = [];
      const step = Math.max(1, Math.floor(data.length / barCount));
      for (let i = 0; i < barCount; i++) {
        result.push(data[i * step] || 0);
      }
      return result;
    },
    [barCount]
  );

  const drawWaveform = useCallback(
    (ctx: CanvasRenderingContext2D, canvasWidth: number, canvasHeight: number, data: number[]) => {
      ctx.clearRect(0, 0, canvasWidth, canvasHeight);

      const centerY = canvasHeight / 2;
      const maxAmplitude = canvasHeight * 0.4;
      const smoothedData = smoothData(data);
      smoothDataRef.current = smoothedData;

      const gradient = ctx.createLinearGradient(0, 0, canvasWidth, 0);
      gradient.addColorStop(0, 'hsla(187, 100%, 57%, 0.1)');
      gradient.addColorStop(
        0.5,
        isSpeaking ? 'hsla(142, 71%, 45%, 0.6)' : 'hsla(187, 100%, 57%, 0.5)'
      );
      gradient.addColorStop(1, 'hsla(187, 100%, 57%, 0.1)');

      // Top wave
      ctx.beginPath();
      ctx.moveTo(0, centerY);
      const segmentWidth = canvasWidth / (smoothedData.length - 1);
      for (let i = 0; i < smoothedData.length; i++) {
        const x = i * segmentWidth;
        const amplitude = (smoothedData[i] / 255) * maxAmplitude;
        const y = centerY + Math.sin(i * 0.5 + Date.now() * 0.002) * amplitude;
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          const prevX = (i - 1) * segmentWidth;
          const prevAmplitude = (smoothedData[i - 1] / 255) * maxAmplitude;
          const prevY = centerY + Math.sin((i - 1) * 0.5 + Date.now() * 0.002) * prevAmplitude;
          ctx.bezierCurveTo(prevX + segmentWidth / 3, prevY, x - segmentWidth / 3, y, x, y);
        }
      }
      ctx.strokeStyle = gradient;
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Bottom wave (mirrored)
      ctx.beginPath();
      ctx.moveTo(0, centerY);
      for (let i = 0; i < smoothedData.length; i++) {
        const x = i * segmentWidth;
        const amplitude = (smoothedData[i] / 255) * maxAmplitude;
        const y = centerY - Math.sin(i * 0.5 + Date.now() * 0.002) * amplitude;
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          const prevX = (i - 1) * segmentWidth;
          const prevAmplitude = (smoothedData[i - 1] / 255) * maxAmplitude;
          const prevY = centerY - Math.sin((i - 1) * 0.5 + Date.now() * 0.002) * prevAmplitude;
          ctx.bezierCurveTo(prevX + segmentWidth / 3, prevY, x - segmentWidth / 3, y, x, y);
        }
      }
      ctx.strokeStyle = gradient;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Center line
      ctx.beginPath();
      ctx.moveTo(0, centerY);
      ctx.lineTo(canvasWidth, centerY);
      ctx.strokeStyle = 'hsla(0, 0%, 100%, 0.05)';
      ctx.lineWidth = 1;
      ctx.stroke();

      if (isSpeaking) {
        ctx.shadowColor = 'hsla(142, 71%, 45%, 0.5)';
        ctx.shadowBlur = 15;
      }
    },
    [smoothData, isSpeaking]
  );

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const animate = () => {
      if (!active) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        return;
      }

      const sampledData = sampleFrequencyData(frequencyData);
      const hasData = sampledData.some((v) => v > 0);
      setInternalActive(hasData);

      const data =
        sampledData.length > 0
          ? sampledData
          : Array.from({ length: barCount }, (_, i) => {
              const time = Date.now() / 1000;
              const wave1 = Math.sin(time * 2 + i * 0.2) * 0.3 + 0.3;
              const wave2 = Math.sin(time * 1.5 + i * 0.15) * 0.2;
              return Math.max(0, (wave1 + wave2) * 255 * 0.3);
            });

      drawWaveform(ctx, canvas.width, canvas.height, data);
      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [active, barCount, drawWaveform, frequencyData, sampleFrequencyData]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={cn('relative overflow-hidden rounded-xl', className)}
    >
      <div
        className="absolute inset-0 rounded-xl"
        style={{
          background: 'linear-gradient(180deg, hsla(230, 20%, 8%, 0.8) 0%, hsla(230, 20%, 8%, 0.6) 100%)',
          border: '1px solid hsla(0, 0%, 100%, 0.06)',
        }}
      />
      <canvas
        ref={canvasRef}
        width={responsive ? undefined : width}
        height={responsive ? undefined : height}
        className={cn('relative z-10 w-full', responsive ? 'h-24 sm:h-28' : '')}
        style={!responsive ? { width, height } : undefined}
        role="img"
        aria-label={active ? 'Real-time audio visualization showing voice waveform' : 'Audio visualization placeholder'}
      />
      <div className="absolute top-3 right-3 flex items-center gap-2">
        <div className={cn('w-1.5 h-1.5 rounded-full', active ? (isSpeaking ? 'bg-emerald-400' : 'bg-cyan-400') : 'bg-zinc-600')} />
        <span className="font-mono text-[10px] uppercase tracking-wider text-zinc-500">
          {active ? (isSpeaking ? 'Active' : 'Listening') : 'Standby'}
        </span>
      </div>
      {active && (
        <motion.div
          className="absolute inset-0 rounded-xl pointer-events-none"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            boxShadow: isSpeaking
              ? 'inset 0 0 20px hsla(142, 71%, 45%, 0.1)'
              : 'inset 0 0 20px hsla(187, 100%, 57%, 0.05)',
          }}
        />
      )}
    </motion.div>
  );
}
