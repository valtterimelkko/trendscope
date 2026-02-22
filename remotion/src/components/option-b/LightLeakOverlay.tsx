import React from 'react';
import { interpolate, Easing } from 'remotion';

interface LightLeakOverlayProps {
  frame: number;
  duration: number;
  direction?: 'left' | 'right' | 'top' | 'bottom';
}

export const LightLeakOverlay: React.FC<LightLeakOverlayProps> = ({ frame, duration, direction = 'left' }) => {
  const progress = interpolate(frame, [0, duration], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) });
  let translateX = 0, translateY = 0;
  switch (direction) {
    case 'left': translateX = interpolate(progress, [0, 0.5, 1], [-1920, 0, 1920], { easing: Easing.inOut(Easing.cubic) }); break;
    case 'right': translateX = interpolate(progress, [0, 0.5, 1], [1920, 0, -1920], { easing: Easing.inOut(Easing.cubic) }); break;
    case 'top': translateY = interpolate(progress, [0, 0.5, 1], [-1080, 0, 1080], { easing: Easing.inOut(Easing.cubic) }); break;
    case 'bottom': translateY = interpolate(progress, [0, 0.5, 1], [1080, 0, -1080], { easing: Easing.inOut(Easing.cubic) }); break;
  }
  const opacity = interpolate(progress, [0, 0.3, 0.5, 0.7, 1], [0, 0.6, 0.8, 0.6, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const gradientDirection = direction === 'left' ? '90deg' : direction === 'right' ? '270deg' : direction === 'top' ? '180deg' : '0deg';

  return (
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', mixBlendMode: 'screen', opacity, transform: `translate(${translateX}px, ${translateY}px)` }}>
      <div style={{ position: 'absolute', width: '60%', height: '120%', background: `linear-gradient(${gradientDirection}, transparent 0%, rgba(245, 158, 11, 0.4) 20%, rgba(252, 211, 77, 0.6) 40%, rgba(245, 158, 11, 0.4) 60%, transparent 100%)`, filter: 'blur(60px)' }} />
      <div style={{ position: 'absolute', width: '30%', height: '100%', left: '20%', background: 'radial-gradient(ellipse 50% 80% at center, rgba(252, 211, 77, 0.3) 0%, transparent 70%)', filter: 'blur(40px)' }} />
      <div style={{ position: 'absolute', width: '100%', height: '20%', top: '40%', background: 'linear-gradient(90deg, transparent 0%, rgba(245, 158, 11, 0.2) 30%, rgba(252, 211, 77, 0.3) 50%, rgba(245, 158, 11, 0.2) 70%, transparent 100%)', filter: 'blur(20px)' }} />
    </div>
  );
};
