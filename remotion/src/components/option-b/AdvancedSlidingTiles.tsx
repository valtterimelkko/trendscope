import React from 'react';
import { interpolate, Easing } from 'remotion';

interface AdvancedSlidingTilesProps {
  fromImage: string;
  toImage: string;
  frame: number;
  duration: number;
}

const NUM_STRIPS = 7;
const STRIP_HEIGHT = 1080 / NUM_STRIPS;

export const AdvancedSlidingTiles: React.FC<AdvancedSlidingTilesProps> = ({ fromImage, toImage, frame, duration }) => {
  const strips = Array.from({ length: NUM_STRIPS }, (_, i) => ({ index: i, direction: i % 2 === 0 ? 'right' : 'left', delay: i * 2, rotation: (i % 2 === 0 ? 1 : -1) * (0.5 + Math.random() * 1) }));

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden' }}>
      <div style={{ position: 'absolute', inset: 0, backgroundImage: `url(${fromImage})`, backgroundSize: 'cover', backgroundPosition: 'center' }} />
      {strips.map((strip) => {
        const stripProgress = interpolate(frame, [strip.delay, duration - (NUM_STRIPS - strip.index) * 2], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
        const translateX = strip.direction === 'left' ? interpolate(stripProgress, [0, 1], [1920, 0], { easing: Easing.out(Easing.cubic) }) : interpolate(stripProgress, [0, 1], [-1920, 0], { easing: Easing.out(Easing.cubic) });
        const opacity = interpolate(stripProgress, [0, 0.3], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        return (
          <div key={strip.index} style={{ position: 'absolute', left: translateX, top: strip.index * STRIP_HEIGHT, width: 1920, height: STRIP_HEIGHT + 2, opacity, transform: `rotate(${strip.rotation * (1 - stripProgress)}deg)`, overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: -strip.index * STRIP_HEIGHT, left: 0, width: 1920, height: 1080, backgroundImage: `url(${toImage})`, backgroundSize: 'cover', backgroundPosition: 'center' }} />
          </div>
        );
      })}
      <div style={{ position: 'absolute', inset: 0, boxShadow: 'inset 0 0 150px rgba(0,0,0,0.5)', pointerEvents: 'none' }} />
    </div>
  );
};
