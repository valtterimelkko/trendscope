import React, { useMemo } from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';

interface ParticleFieldProps {
  particleCount?: number;
  className?: string;
}

const COLORS = {
  accentCyan: '#00D9FF',
  accentBlue: '#3B82F6',
};

interface Particle {
  id: number;
  x: number;
  size: number;
  speed: number;
  delay: number;
  opacity: number;
  drift: number;
  layer: number; // 0 = far, 1 = mid, 2 = near
}

export const ParticleField: React.FC<ParticleFieldProps> = ({ 
  particleCount = 60,
}) => {
  const frame = useCurrentFrame();

  // Generate particles with varying depths
  const particles = useMemo<Particle[]>(() => {
    return Array.from({ length: particleCount }, (_, i) => {
      const layer = i % 3; // 0 = far, 1 = mid, 2 = near
      const baseSize = layer === 0 ? 2 : layer === 1 ? 4 : 6;
      const baseSpeed = layer === 0 ? 180 : layer === 1 ? 120 : 80;
      const baseOpacity = layer === 0 ? 0.4 : layer === 1 ? 0.7 : 1;
      
      return {
        id: i,
        x: 100 + (i % 12) * 160 + Math.random() * 80,
        size: baseSize + Math.random() * (layer === 2 ? 4 : 2),
        speed: baseSpeed + Math.random() * 40,
        delay: i * 1.5 + Math.random() * 20,
        opacity: baseOpacity,
        drift: (Math.random() - 0.5) * 30,
        layer,
      };
    });
  }, [particleCount]);

  return (
    <div
      style={{
        position: 'absolute',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        pointerEvents: 'none',
      }}
    >
      {particles.map((particle) => {
        const y = interpolate(
          frame,
          [particle.delay, particle.delay + particle.speed],
          [1150, -150],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.linear }
        );

        const xOffset = interpolate(
          frame,
          [particle.delay, particle.delay + particle.speed],
          [0, particle.drift],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        // Fade in/out at edges with blur for depth
        const fadeInStart = particle.delay;
        const fadeInEnd = particle.delay + 20;
        const fadeOutStart = particle.delay + particle.speed - 30;
        const fadeOutEnd = particle.delay + particle.speed;

        const opacity = interpolate(
          frame,
          [fadeInStart, fadeInEnd, fadeOutStart, fadeOutEnd],
          [0, particle.opacity, particle.opacity, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        // Blur based on layer (depth of field effect)
        const blurAmount = particle.layer === 0 ? 3 : particle.layer === 1 ? 1.5 : 0;
        
        // Glow intensity based on layer
        const glowIntensity = particle.layer === 2 ? 15 : particle.layer === 1 ? 10 : 5;

        return (
          <div
            key={particle.id}
            style={{
              position: 'absolute',
              left: particle.x + xOffset,
              top: y,
              width: particle.size,
              height: particle.size,
              backgroundColor: particle.layer === 0 ? COLORS.accentBlue : COLORS.accentCyan,
              borderRadius: '50%',
              opacity,
              filter: `blur(${blurAmount}px) drop-shadow(0 0 ${glowIntensity}px ${particle.layer === 0 ? COLORS.accentBlue : COLORS.accentCyan})`,
              boxShadow: `0 0 ${glowIntensity}px ${particle.layer === 0 ? COLORS.accentBlue : COLORS.accentCyan}`,
              transform: `translateZ(${particle.layer * 10}px)`,
              zIndex: particle.layer,
            }}
          />
        );
      })}
    </div>
  );
};
