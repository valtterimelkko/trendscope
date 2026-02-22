import React from 'react';
import { Img, staticFile } from 'remotion';
import { interpolate, Easing } from 'remotion';

interface KenBurnsImageProps {
  src: string;
  frame: number;
  duration: number;
  direction?: 'in' | 'out' | 'left' | 'right';
}

export const KenBurnsImage: React.FC<KenBurnsImageProps> = ({ src, frame, duration, direction = 'in' }) => {
  const progress = frame / duration;
  let scale = 1, translateX = 0, translateY = 0;
  switch (direction) {
    case 'in': scale = interpolate(progress, [0, 1], [1.15, 1], { easing: Easing.out(Easing.cubic) }); break;
    case 'out': scale = interpolate(progress, [0, 1], [1, 1.15], { easing: Easing.out(Easing.cubic) }); break;
    case 'left': scale = interpolate(progress, [0, 1], [1.1, 1.05], { easing: Easing.out(Easing.cubic) }); translateX = interpolate(progress, [0, 1], [30, -30], { easing: Easing.out(Easing.cubic) }); break;
    case 'right': scale = interpolate(progress, [0, 1], [1.1, 1.05], { easing: Easing.out(Easing.cubic) }); translateX = interpolate(progress, [0, 1], [-30, 30], { easing: Easing.out(Easing.cubic) }); break;
  }
  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden' }}>
      <Img src={staticFile(src)} style={{ width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`, transition: 'none' }} />
    </div>
  );
};
