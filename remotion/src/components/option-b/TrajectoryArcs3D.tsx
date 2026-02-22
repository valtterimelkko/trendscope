import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';

const COLORS = { accentCyan: '#00D9FF', accentOrange: '#F59E0B', accentBlue: '#3B82F6' };

export const TrajectoryArcs: React.FC = () => {
  const frame = useCurrentFrame();
  const arcs = [
    { startX: 350, startY: 350, endX: 100, endY: 150, color: COLORS.accentCyan, delay: 0 },
    { startX: 350, startY: 350, endX: 600, endY: 100, color: COLORS.accentOrange, delay: 10 },
    { startX: 350, startY: 350, endX: 650, endY: 350, color: COLORS.accentCyan, delay: 20 },
    { startX: 350, startY: 350, endX: 550, endY: 600, color: COLORS.accentOrange, delay: 30 },
    { startX: 350, startY: 350, endX: 150, endY: 550, color: COLORS.accentBlue, delay: 40 },
  ];

  return (
    <svg style={{ position: 'absolute', left: 100, top: '50%', transform: 'translateY(-50%)', width: 700, height: 700, pointerEvents: 'none' }}>
      <defs>
        {arcs.map((arc, index) => (
          <linearGradient key={index} id={`arc-grad-${index}`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={arc.color} stopOpacity="0.8" />
            <stop offset="100%" stopColor={arc.color} stopOpacity="0.2" />
          </linearGradient>
        ))}
      </defs>
      {arcs.map((arc, index) => {
        const drawProgress = interpolate(frame, [25 + arc.delay, 70 + arc.delay], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        const controlX = (arc.startX + arc.endX) / 2 + (index % 2 === 0 ? 100 : -100);
        const controlY = (arc.startY + arc.endY) / 2 - 50;
        const t = drawProgress;
        const invT = 1 - t;
        const currentX = invT * invT * arc.startX + 2 * invT * t * controlX + t * t * arc.endX;
        const currentY = invT * invT * arc.startY + 2 * invT * t * controlY + t * t * arc.endY;
        const path = `M ${arc.startX},${arc.startY} Q ${controlX},${controlY} ${currentX},${currentY}`;
        return (
          <g key={index}>
            <path d={path} stroke={`url(#arc-grad-${index})`} strokeWidth={3} fill="none" filter="drop-shadow(0 0 8px currentColor)" />
            <path d={path} stroke={arc.color} strokeWidth={8} fill="none" opacity={0.3} filter="blur(4px)" />
          </g>
        );
      })}
    </svg>
  );
};
