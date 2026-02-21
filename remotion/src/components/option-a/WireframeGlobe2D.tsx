import React from 'react';
import { useCurrentFrame, interpolate, Easing, Img, staticFile } from 'remotion';

interface WireframeGlobe2DProps {
  globeUrl: string;
  className?: string;
}

const COLORS = {
  accentCyan: '#00D9FF',
  accentOrange: '#F59E0B',
};

export const WireframeGlobe2D: React.FC<WireframeGlobe2DProps> = ({ globeUrl }) => {
  const frame = useCurrentFrame();

  // Globe rotation animation
  const globeRotation = interpolate(
    frame,
    [0, 180],
    [0, 120],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.linear }
  );

  // Globe scale animation (entrance)
  const globeScale = interpolate(
    frame,
    [0, 40],
    [0.8, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Globe opacity animation (entrance)
  const globeOpacity = interpolate(
    frame,
    [0, 30],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <div
      style={{
        position: 'relative',
        width: 700,
        height: 700,
        perspective: '1000px',
      }}
    >
      {/* 3D Rotating Container */}
      <div
        style={{
          width: '100%',
          height: '100%',
          transformStyle: 'preserve-3d',
          transform: `rotateY(${globeRotation}deg) scale(${globeScale})`,
          opacity: globeOpacity,
          transition: 'none', // Ensure no CSS transitions interfere
        }}
      >
        {/* Globe Image */}
        <Img
          src={staticFile(globeUrl)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            filter: 'drop-shadow(0 0 30px rgba(0, 217, 255, 0.4))',
          }}
        />

        {/* Glowing Data Points at City Locations */}
        <CityPoints frame={frame} />

        {/* Trajectory Arcs */}
        <TrajectoryArcs frame={frame} />
      </div>
    </div>
  );
};

// City data points that appear on the globe
const CityPoints: React.FC<{ frame: number }> = ({ frame }) => {
  const cities = [
    { id: 1, x: 350, y: 250, delay: 40 },
    { id: 2, x: 450, y: 300, delay: 50 },
    { id: 3, x: 250, y: 350, delay: 60 },
    { id: 4, x: 400, y: 400, delay: 70 },
    { id: 5, x: 300, y: 450, delay: 80 },
  ];

  return (
    <>
      {cities.map((city) => {
        const opacity = interpolate(
          frame,
          [city.delay, city.delay + 20],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        const pulse = interpolate(
          frame,
          [city.delay, city.delay + 30],
          [0.5, 1.2],
          { extrapolateLeft: 'clamp', extrapolateRight: 'extend' }
        );

        return (
          <div
            key={city.id}
            style={{
              position: 'absolute',
              left: city.x - 8,
              top: city.y - 8,
              width: 16,
              height: 16,
              opacity,
            }}
          >
            {/* Outer pulse ring */}
            <div
              style={{
                position: 'absolute',
                left: '50%',
                top: '50%',
                transform: `translate(-50%, -50%) scale(${pulse})`,
                width: 24,
                height: 24,
                borderRadius: '50%',
                border: `2px solid ${COLORS.accentCyan}`,
                opacity: 0.5,
              }}
            />
            {/* Inner dot */}
            <div
              style={{
                position: 'absolute',
                left: '50%',
                top: '50%',
                transform: 'translate(-50%, -50%)',
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: COLORS.accentCyan,
                boxShadow: `0 0 15px ${COLORS.accentCyan}`,
              }}
            />
          </div>
        );
      })}
    </>
  );
};

// Animated trajectory arcs emanating from the globe
const TrajectoryArcs: React.FC<{ frame: number }> = ({ frame }) => {
  const arcs = [
    { id: 1, startX: 350, startY: 200, endX: 750, endY: 100, color: COLORS.accentCyan, delay: 60 },
    { id: 2, startX: 400, startY: 250, endX: 780, endY: 300, color: COLORS.accentOrange, delay: 75 },
    { id: 3, startX: 300, startY: 350, endX: 720, endY: 450, color: COLORS.accentCyan, delay: 90 },
    { id: 4, startX: 380, startY: 420, endX: 760, endY: 550, color: COLORS.accentOrange, delay: 105 },
    { id: 5, startX: 320, startY: 500, endX: 700, endY: 650, color: COLORS.accentCyan, delay: 120 },
  ];

  return (
    <svg
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        width: '100%',
        height: '100%',
        overflow: 'visible',
        pointerEvents: 'none',
      }}
    >
      <defs>
        {/* Glow filter for arcs */}
        <filter id="arcGlow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {arcs.map((arc) => {
        // Calculate bezier control point for curved arc
        const midX = (arc.startX + arc.endX) / 2;
        const midY = (arc.startY + arc.endY) / 2;
        const controlX = midX + 50;
        const controlY = midY - 100;

        // Draw-on animation using stroke-dasharray
        const pathLength = Math.sqrt(
          Math.pow(arc.endX - arc.startX, 2) + Math.pow(arc.endY - arc.startY, 2)
        ) * 1.5; // Approximation

        const drawProgress = interpolate(
          frame,
          [arc.delay, arc.delay + 30],
          [0, pathLength],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
        );

        const opacity = interpolate(
          frame,
          [arc.delay, arc.delay + 15],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        return (
          <g key={arc.id} opacity={opacity}>
            {/* Main arc path */}
            <path
              d={`M ${arc.startX},${arc.startY} Q ${controlX},${controlY} ${arc.endX},${arc.endY}`}
              fill="none"
              stroke={arc.color}
              strokeWidth={3}
              filter="url(#arcGlow)"
              strokeLinecap="round"
              strokeDasharray={pathLength}
              strokeDashoffset={pathLength - drawProgress}
            />

            {/* Leading glow point */}
            {drawProgress > pathLength * 0.1 && (
              <circle
                cx={arc.endX}
                cy={arc.endY}
                r={8}
                fill={arc.color}
                opacity={0.9}
                filter="url(#arcGlow)"
              />
            )}
          </g>
        );
      })}
    </svg>
  );
};
