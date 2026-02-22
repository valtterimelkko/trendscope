import React, { useMemo } from 'react';
import { useCurrentFrame, interpolate } from 'remotion';

const COLORS = { accentCyan: '#00D9FF', accentBlue: '#3B82F6' };

interface Particle { id: number; x: number; depth: number; size: number; speed: number; delay: number; color: string; }

export const ParticleField3D: React.FC = () => {
  const frame = useCurrentFrame();
  const particles = useMemo<Particle[]>(() => {
    return Array.from({ length: 60 }, (_, i) => {
      const depth = Math.random();
      const isForeground = depth < 0.3;
      return { id: i, x: 100 + (i % 12) * 160 + Math.random() * 80, depth, size: isForeground ? 3 + Math.random() * 4 : 1.5 + Math.random() * 2.5, speed: 0.8 + depth * 0.5, delay: i * 1.5, color: Math.random() > 0.5 ? COLORS.accentCyan : COLORS.accentBlue };
    });
  }, []);

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {particles.map((particle) => {
        const y = interpolate(frame, [particle.delay, particle.delay + 150 * particle.speed], [1100, -100], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        const opacity = interpolate(frame, [particle.delay, particle.delay + 20, particle.delay + 100 * particle.speed, particle.delay + 130 * particle.speed], [0, particle.depth < 0.3 ? 0.9 : 0.6, particle.depth < 0.3 ? 0.9 : 0.6, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        const blur = particle.depth * 3;
        const glowSize = particle.depth < 0.3 ? 15 : 8;
        return (
          <div key={particle.id} style={{ position: 'absolute', left: particle.x, top: y, width: particle.size, height: particle.size, backgroundColor: particle.color, borderRadius: '50%', opacity, filter: `blur(${blur}px)`, boxShadow: `0 0 ${glowSize}px ${particle.color}` }} />
        );
      })}
    </div>
  );
};
