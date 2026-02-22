import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';

const COLORS = { accentCyan: '#00D9FF', accentBlue: '#3B82F6' };

const rings = [
  { size: 550, color: COLORS.accentCyan, rotationSpeed: 1, direction: 1, opacity: 0.7, blur: 0, delay: 0 },
  { size: 650, color: COLORS.accentCyan, rotationSpeed: 0.7, direction: -1, opacity: 0.4, blur: 10, delay: 5 },
  { size: 800, color: COLORS.accentBlue, rotationSpeed: 0.5, direction: 1, opacity: 0.25, blur: 25, delay: 10 },
  { size: 950, color: COLORS.accentBlue, rotationSpeed: 0.3, direction: -1, opacity: 0.15, blur: 40, delay: 15 },
];

export const VolumetricRings: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{ position: 'absolute', inset: 0, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      {rings.map((ring, index) => {
        const rotation = interpolate(frame, [ring.delay, ring.delay + 180 * (1 / ring.rotationSpeed)], [0, 360 * ring.direction], { extrapolateRight: 'extend' });
        return (
          <div key={index} style={{ position: 'absolute', width: ring.size, height: ring.size, border: `${index === 0 ? 3 : 2}px solid ${ring.color}`, borderRadius: '50%', opacity: ring.opacity, transform: `rotate(${rotation}deg)`, filter: `blur(${ring.blur}px) drop-shadow(0 0 ${20 + ring.blur}px ${ring.color}40)`, boxShadow: `0 0 ${40 + index * 20}px ${ring.color}${Math.floor(ring.opacity * 40).toString(16).padStart(2, '0')}` }} />
        );
      })}
    </div>
  );
};
