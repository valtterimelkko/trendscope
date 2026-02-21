import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';

interface OrbitalRingsEnhancedProps {
  className?: string;
}

const COLORS = {
  accentCyan: '#00D9FF',
  accentBlue: '#3B82F6',
};

export const OrbitalRingsEnhanced: React.FC<OrbitalRingsEnhancedProps> = () => {
  const frame = useCurrentFrame();

  // Ring 1 (Left, Cyan) - Rotates clockwise with varying speed
  const ring1Rotation = interpolate(
    frame,
    [0, 180],
    [0, 360],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.sin) }
  );

  // Ring 2 (Right, Blue) - Rotates counter-clockwise
  const ring2Rotation = interpolate(
    frame,
    [0, 180],
    [0, -360],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.sin) }
  );

  // Ring opacity animation
  const ring1Opacity = interpolate(
    frame,
    [0, 30],
    [0, 0.7],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const ring2Opacity = interpolate(
    frame,
    [10, 40],
    [0, 0.6],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <svg
      style={{
        position: 'absolute',
        width: '100%',
        height: '100%',
        overflow: 'visible',
      }}
    >
      <defs>
        {/* Gradient for Ring 1 - Cyan to Blue */}
        <linearGradient id="ringGradient1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={COLORS.accentCyan} stopOpacity="1" />
          <stop offset="50%" stopColor="#1E90FF" stopOpacity="0.8" />
          <stop offset="100%" stopColor={COLORS.accentBlue} stopOpacity="0.6" />
        </linearGradient>

        {/* Gradient for Ring 2 - Blue to Cyan */}
        <linearGradient id="ringGradient2" x1="100%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={COLORS.accentBlue} stopOpacity="1" />
          <stop offset="50%" stopColor="#1E90FF" stopOpacity="0.8" />
          <stop offset="100%" stopColor={COLORS.accentCyan} stopOpacity="0.6" />
        </linearGradient>

        {/* Glow filter for rings */}
        <filter id="ringGlow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="15" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        {/* Outer halo filter */}
        <filter id="haloGlow" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation="25" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="blur" />
          </feMerge>
        </filter>
      </defs>

      {/* Outer halo for Ring 1 */}
      <ellipse
        cx={450}
        cy={540}
        rx={380}
        ry={380}
        fill="none"
        stroke={COLORS.accentCyan}
        strokeWidth={2}
        opacity={ring1Opacity * 0.2}
        filter="url(#haloGlow)"
        transform={`rotate(${ring1Rotation}, 450, 540)`}
      />

      {/* Main Ring 1 (Cyan, Left) */}
      <ellipse
        cx={450}
        cy={540}
        rx={350}
        ry={350}
        fill="none"
        stroke="url(#ringGradient1)"
        strokeWidth={10}
        opacity={ring1Opacity}
        filter="url(#ringGlow)"
        transform={`rotate(${ring1Rotation}, 450, 540)`}
        style={{
          transformOrigin: '450px 540px',
        }}
      />

      {/* Inner accent ring for Ring 1 */}
      <ellipse
        cx={450}
        cy={540}
        rx={320}
        ry={320}
        fill="none"
        stroke={COLORS.accentCyan}
        strokeWidth={3}
        opacity={ring1Opacity * 0.4}
        transform={`rotate(${ring1Rotation + 45}, 450, 540)`}
        style={{
          transformOrigin: '450px 540px',
        }}
      />

      {/* Outer halo for Ring 2 */}
      <ellipse
        cx={1470}
        cy={540}
        rx={330}
        ry={330}
        fill="none"
        stroke={COLORS.accentBlue}
        strokeWidth={2}
        opacity={ring2Opacity * 0.2}
        filter="url(#haloGlow)"
        transform={`rotate(${ring2Rotation}, 1470, 540)`}
      />

      {/* Main Ring 2 (Blue, Right) */}
      <ellipse
        cx={1470}
        cy={540}
        rx={300}
        ry={300}
        fill="none"
        stroke="url(#ringGradient2)"
        strokeWidth={10}
        opacity={ring2Opacity}
        filter="url(#ringGlow)"
        transform={`rotate(${ring2Rotation}, 1470, 540)`}
        style={{
          transformOrigin: '1470px 540px',
        }}
      />

      {/* Inner accent ring for Ring 2 */}
      <ellipse
        cx={1470}
        cy={540}
        rx={270}
        ry={270}
        fill="none"
        stroke={COLORS.accentBlue}
        strokeWidth={3}
        opacity={ring2Opacity * 0.4}
        transform={`rotate(${ring2Rotation - 45}, 1470, 540)`}
        style={{
          transformOrigin: '1470px 540px',
        }}
      />
    </svg>
  );
};
