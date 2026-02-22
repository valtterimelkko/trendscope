import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';

const COLORS = {
  accentCyan: '#00D9FF',
  accentBlue: '#3B82F6',
};

const sweepLines = [
  { id: 1, delay: 0, duration: 60, startY: 200, endY: 300, controlY: 100, color: COLORS.accentCyan, width: 3 },
  { id: 2, delay: 15, duration: 70, startY: 400, endY: 500, controlY: 200, color: COLORS.accentBlue, width: 2 },
  { id: 3, delay: 30, duration: 65, startY: 600, endY: 700, controlY: 800, color: COLORS.accentCyan, width: 2.5 },
  { id: 4, delay: 45, duration: 75, startY: 350, endY: 250, controlY: 450, color: COLORS.accentBlue, width: 2 },
];

export const TrailSweepLines: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
      <defs>
        {sweepLines.map((line) => (
          <linearGradient key={line.id} id={`trail-gradient-${line.id}`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={line.color} stopOpacity="0" />
            <stop offset="30%" stopColor={line.color} stopOpacity="0.6" />
            <stop offset="50%" stopColor={line.color} stopOpacity="0.9" />
            <stop offset="70%" stopColor={line.color} stopOpacity="0.6" />
            <stop offset="100%" stopColor={line.color} stopOpacity="0" />
          </linearGradient>
        ))}
        <filter id="motion-blur"><feGaussianBlur in="SourceGraphic" stdDeviation="2,0" /></filter>
      </defs>
      {sweepLines.map((line) => {
        const progress = interpolate(frame, [line.delay, line.delay + line.duration], [-300, 2220], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.quad) });
        const opacity = interpolate(frame, [line.delay, line.delay + 10, line.delay + line.duration - 10, line.delay + line.duration], [0, 0.8, 0.8, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        const path = `M ${progress - 200},${line.startY} Q ${progress + 480},${line.controlY} ${progress + 1160},${line.endY}`;
        return (
          <g key={line.id} opacity={opacity}>
            <path d={path} stroke={`url(#trail-gradient-${line.id})`} strokeWidth={line.width} fill="none" filter="url(#motion-blur)" />
            <path d={path} stroke={line.color} strokeWidth={line.width * 3} fill="none" opacity={0.3} filter="blur(4px)" />
          </g>
        );
      })}
    </svg>
  );
};
