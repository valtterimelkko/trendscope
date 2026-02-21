import React from 'react';
import { useCurrentFrame, interpolate, Easing, Img, staticFile } from 'remotion';

interface SlidingTilesProps {
  fromImage: string;
  toImage: string;
  startFrame: number;
  duration?: number;
}

interface StripConfig {
  index: number;
  direction: 'left' | 'right';
  delay: number;
}

export const SlidingTiles: React.FC<SlidingTilesProps> = ({
  fromImage,
  toImage,
  startFrame,
  duration = 30,
}) => {
  const frame = useCurrentFrame();
  const localFrame = frame - startFrame;

  // Split screen into 5 horizontal strips
  const stripHeight = 216; // 1080 / 5
  const strips: StripConfig[] = [
    { index: 0, direction: 'right', delay: 0 },
    { index: 1, direction: 'left', delay: 3 },
    { index: 2, direction: 'right', delay: 6 },
    { index: 3, direction: 'left', delay: 9 },
    { index: 4, direction: 'right', delay: 12 },
  ];

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        zIndex: 100,
      }}
    >
      {strips.map((strip) => {
        const stripTop = strip.index * stripHeight;
        const delay = strip.delay;
        
        // Calculate progress with easing
        const rawProgress = interpolate(
          localFrame,
          [delay, duration + delay - 5],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        const progress = Easing.out(Easing.cubic)(rawProgress);

        // From image slides out
        const fromTranslateX = strip.direction === 'left' 
          ? interpolate(progress, [0, 1], [0, -1920])
          : interpolate(progress, [0, 1], [0, 1920]);

        // To image slides in
        const toTranslateX = strip.direction === 'left'
          ? interpolate(progress, [0, 1], [1920, 0])
          : interpolate(progress, [0, 1], [-1920, 0]);

        // Fade out the from image
        const fromOpacity = interpolate(
          progress,
          [0, 0.7],
          [1, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        // Fade in the to image
        const toOpacity = interpolate(
          progress,
          [0.3, 1],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        return (
          <div
            key={strip.index}
            style={{
              position: 'absolute',
              left: 0,
              top: stripTop,
              width: 1920,
              height: stripHeight,
              overflow: 'hidden',
            }}
          >
            {/* From image strip */}
            <div
              style={{
                position: 'absolute',
                left: 0,
                top: -stripTop,
                width: 1920,
                height: 1080,
                transform: `translateX(${fromTranslateX}px)`,
                opacity: fromOpacity,
              }}
            >
              <Img
                src={staticFile(fromImage)}
                style={{
                  width: 1920,
                  height: 1080,
                  objectFit: 'cover',
                }}
              />
            </div>

            {/* To image strip */}
            <div
              style={{
                position: 'absolute',
                left: 0,
                top: -stripTop,
                width: 1920,
                height: 1080,
                transform: `translateX(${toTranslateX}px)`,
                opacity: toOpacity,
              }}
            >
              <Img
                src={staticFile(toImage)}
                style={{
                  width: 1920,
                  height: 1080,
                  objectFit: 'cover',
                }}
              />
            </div>

            {/* Subtle edge shadow for depth */}
            <div
              style={{
                position: 'absolute',
                left: 0,
                top: 0,
                width: '100%',
                height: '100%',
                boxShadow: 'inset 0 2px 10px rgba(0,0,0,0.3)',
                pointerEvents: 'none',
              }}
            />
          </div>
        );
      })}
    </div>
  );
};

// Simple sliding transition wrapper for scenes
interface SlidingTransitionProps {
  children: React.ReactNode;
  direction?: 'left' | 'right';
  delay?: number;
  duration?: number;
}

export const SlidingTransition: React.FC<SlidingTransitionProps> = ({
  children,
  direction = 'right',
  delay = 0,
  duration = 20,
}) => {
  const frame = useCurrentFrame();

  const translateX = interpolate(
    frame,
    [delay, delay + duration],
    direction === 'left' ? [1920, 0] : [-1920, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  const opacity = interpolate(
    frame,
    [delay, delay + 10],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        transform: `translateX(${translateX}px)`,
        opacity,
      }}
    >
      {children}
    </div>
  );
};
