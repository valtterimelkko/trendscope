import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';

const COLORS = { bgDark: '#020617', bgMid: '#0a1628', accentCyan: '#00D9FF' };

export const CinematicBackground: React.FC = () => {
  const frame = useCurrentFrame();
  const gradientShift = interpolate(frame, [0, 300], [0, 100], { extrapolateRight: 'extend' });
  const glowIntensity = interpolate(frame, [0, 60, 120, 180], [0.08, 0.15, 0.12, 0.1], { extrapolateRight: 'clamp' });
  return (
    <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(ellipse 80% 60% at ${50 + gradientShift * 0.1}% 50%, rgba(0, 217, 255, ${glowIntensity}) 0%, transparent 60%), radial-gradient(ellipse 120% 100% at 30% 20%, ${COLORS.bgMid} 0%, ${COLORS.bgDark} 50%), ${COLORS.bgDark}` }} />
  );
};
