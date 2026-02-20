import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  spring,
} from 'remotion';

interface Trend {
  name: string;
  growth: string;
  views: string;
}

interface TrendReportProps {
  title: string;
  subtitle: string;
  trends: Trend[];
}

export const TrendReportVideo: React.FC<TrendReportProps> = ({
  title,
  subtitle,
  trends,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance animation
  const titleY = interpolate(
    frame,
    [0, 30],
    [50, 0],
    {
      easing: Easing.out(Easing.cubic),
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  const titleOpacity = interpolate(
    frame,
    [0, 20],
    [0, 1],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(135deg, #0066FF 0%, #00D9FF 100%)',
        fontFamily: 'Inter, sans-serif',
      }}
    >
      {/* Header */}
      <div
        style={{
          position: 'absolute',
          top: 80,
          left: 80,
          right: 80,
          transform: `translateY(${titleY}px)`,
          opacity: titleOpacity,
        }}
      >
        <h1
          style={{
            fontSize: 72,
            fontWeight: 700,
            color: '#FFFFFF',
            margin: 0,
            marginBottom: 16,
            fontFamily: 'Clash Display, sans-serif',
          }}
        >
          {title}
        </h1>
        <p
          style={{
            fontSize: 32,
            color: 'rgba(255, 255, 255, 0.9)',
            margin: 0,
          }}
        >
          {subtitle}
        </p>
      </div>

      {/* Trend Cards */}
      {trends.map((trend, index) => {
        const delay = index * 10;
        const cardProgress = spring({
          frame: frame - delay - 30,
          fps,
          config: {
            damping: 12,
            stiffness: 100,
          },
        });

        const cardX = interpolate(
          cardProgress,
          [0, 1],
          [100, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        const cardOpacity = interpolate(
          cardProgress,
          [0, 0.5],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        return (
          <div
            key={index}
            style={{
              position: 'absolute',
              left: 80,
              right: 80,
              top: 300 + index * 180,
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              borderRadius: 16,
              padding: 32,
              transform: `translateX(${cardX}px)`,
              opacity: cardOpacity,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.2)',
            }}
          >
            <div>
              <span
                style={{
                  fontSize: 36,
                  fontWeight: 600,
                  color: '#1A1A1A',
                }}
              >
                {trend.name}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 48, alignItems: 'center' }}>
              <div style={{ textAlign: 'center' }}>
                <div
                  style={{
                    fontSize: 24,
                    color: '#00C853',
                    fontWeight: 700,
                  }}
                >
                  {trend.growth}
                </div>
                <div style={{ fontSize: 14, color: '#6B7280' }}>Growth</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div
                  style={{
                    fontSize: 24,
                    color: '#0066FF',
                    fontWeight: 700,
                  }}
                >
                  {trend.views}
                </div>
                <div style={{ fontSize: 14, color: '#6B7280' }}>Views</div>
              </div>
            </div>
          </div>
        );
      })}

      {/* Brand Logo */}
      <div
        style={{
          position: 'absolute',
          bottom: 40,
          right: 80,
          fontSize: 24,
          fontWeight: 600,
          color: 'rgba(255, 255, 255, 0.8)',
        }}
      >
        Trendscope
      </div>
    </AbsoluteFill>
  );
};
