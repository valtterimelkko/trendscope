import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';

interface CurvedSweepLinesProps {
  className?: string;
}

const COLORS = {
  accentCyan: '#00D9FF',
  accentBlue: '#3B82F6',
};

export const CurvedSweepLines: React.FC<CurvedSweepLinesProps> = () => {
  const frame = useCurrentFrame();

  // Define curved sweep paths with quadratic bezier curves
  // Each line sweeps at different speeds and delays
  const sweepLines = [
    {
      id: 1,
      delay: 0,
      speed: 60,
      yBase: 200,
      curve: 'Q 960,100 2120,300',
      color: COLORS.accentCyan,
    },
    {
      id: 2,
      delay: 15,
      speed: 55,
      yBase: 400,
      curve: 'Q 960,200 2120,500',
      color: COLORS.accentBlue,
    },
    {
      id: 3,
      delay: 30,
      speed: 65,
      yBase: 600,
      curve: 'Q 960,800 2120,700',
      color: COLORS.accentCyan,
    },
    {
      id: 4,
      delay: 45,
      speed: 50,
      yBase: 800,
      curve: 'Q 960,700 2120,900',
      color: COLORS.accentBlue,
    },
  ];

  return (
    <svg
      style={{
        position: 'absolute',
        width: '100%',
        height: '100%',
        overflow: 'visible',
        pointerEvents: 'none',
      }}
    >
      <defs>
        {/* Motion blur filter */}
        <filter id="motionBlur" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="8,2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        {/* Trail gradient */}
        <linearGradient id="sweepGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="transparent" />
          <stop offset="20%" stopColor={COLORS.accentCyan} stopOpacity="0.8" />
          <stop offset="80%" stopColor={COLORS.accentCyan} stopOpacity="0.8" />
          <stop offset="100%" stopColor="transparent" />
        </linearGradient>
      </defs>

      {sweepLines.map((line) => {
        const progress = interpolate(
          frame,
          [line.delay, line.delay + line.speed],
          [-400, 2320],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.quad) }
        );

        const opacity = interpolate(
          frame,
          [line.delay, line.delay + 10, line.delay + line.speed - 10, line.delay + line.speed],
          [0, 0.9, 0.9, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        // Trail effect - multiple lines with decreasing opacity
        const trails = [0, -30, -60, -90];

        return (
          <g key={line.id} opacity={opacity}>
            {trails.map((offset, index) => {
              const trailOpacity = 1 - (index * 0.25);
              const trailWidth = 6 - index;
              
              return (
                <path
                  key={index}
                  d={`M ${-400 + progress + offset},${line.yBase} ${line.curve}`}
                  fill="none"
                  stroke={line.color}
                  strokeWidth={trailWidth}
                  opacity={trailOpacity * 0.5}
                  filter={index === 0 ? 'url(#motionBlur)' : undefined}
                  strokeLinecap="round"
                />
              );
            })}
            
            {/* Main line */}
            <path
              d={`M ${-400 + progress},${line.yBase} ${line.curve}`}
              fill="none"
              stroke={line.color}
              strokeWidth={6}
              filter="url(#motionBlur)"
              strokeLinecap="round"
            />

            {/* Glow point at leading edge */}
            <circle
              cx={1920}
              cy={line.yBase + (line.id === 1 ? 100 : line.id === 2 ? 100 : line.id === 3 ? 100 : 100)}
              r={15}
              fill={line.color}
              opacity={0.8}
              filter="url(#motionBlur)"
            >
              <animate
                attributeName="r"
                values="10;20;10"
                dur="0.5s"
                repeatCount="indefinite"
              />
            </circle>
          </g>
        );
      })}
    </svg>
  );
};
