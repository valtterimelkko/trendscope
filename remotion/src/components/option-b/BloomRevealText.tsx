import React from 'react';
import { interpolate, Easing, spring } from 'remotion';

const COLORS = { white: '#FFFFFF', white70: 'rgba(255,255,255,0.7)', accentCyan: '#00D9FF' };

interface BloomRevealTextProps {
  text: string;
  subtext?: string;
  frame: number;
  delay?: number;
  exitStartFrame?: number;
  exitEndFrame?: number;
}

export const BloomRevealText: React.FC<BloomRevealTextProps> = ({ text, subtext, frame, delay = 0, exitStartFrame = 150, exitEndFrame = 180 }) => {
  const textSpring = spring({ frame: frame - delay, fps: 30, config: { damping: 12, stiffness: 100, mass: 0.8 } });
  const titleOpacity = interpolate(frame, [delay, delay + 20, exitStartFrame, exitEndFrame], [0, 1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const titleScale = interpolate(textSpring, [0, 1], [0.85, 1], { easing: Easing.out(Easing.cubic) });
  const titleY = interpolate(frame, [delay, delay + 25], [40, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
  const subtextOpacity = interpolate(frame, [delay + 15, delay + 35, exitStartFrame - 10, exitEndFrame - 10], [0, 1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const subtextY = interpolate(frame, [delay + 15, delay + 35], [30, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });

  return (
    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
      <h1 style={{ fontSize: 56, fontWeight: 800, color: COLORS.white, letterSpacing: '0.15em', textTransform: 'uppercase', fontFamily: 'Inter, system-ui, sans-serif', margin: 0, marginBottom: subtext ? 16 : 0, opacity: titleOpacity, transform: `scale(${titleScale}) translateY(${titleY}px)`, textShadow: `0 0 20px ${COLORS.accentCyan}80, 0 0 40px ${COLORS.accentCyan}60, 0 0 80px ${COLORS.accentCyan}40` }}>{text}</h1>
      {subtext && <p style={{ fontSize: 24, color: COLORS.white70, letterSpacing: '0.05em', fontFamily: 'Inter, system-ui, sans-serif', margin: 0, opacity: subtextOpacity, transform: `translateY(${subtextY}px)` }}>{subtext}</p>}
    </div>
  );
};
