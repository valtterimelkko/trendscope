import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  spring,
  Sequence,
} from 'remotion';

interface MarketingHeroProps {
  headline: string;
  subheadline: string;
  cta: string;
}

export const MarketingHeroVideo: React.FC<MarketingHeroProps> = ({
  headline,
  subheadline,
  cta,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Background animation
  const bgScale = interpolate(
    frame,
    [0, durationInFrames],
    [1, 1.1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Text animations
  const headlineSpring = spring({
    frame: frame - 10,
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  const headlineY = interpolate(
    headlineSpring,
    [0, 1],
    [100, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const headlineOpacity = interpolate(
    frame,
    [10, 30],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Subheadline animation
  const subSpring = spring({
    frame: frame - 40,
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  const subY = interpolate(
    subSpring,
    [0, 1],
    [50, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const subOpacity = interpolate(
    frame,
    [40, 60],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // CTA button animation
  const ctaSpring = spring({
    frame: frame - 80,
    fps,
    config: { damping: 12, stiffness: 150 },
  });

  const ctaScale = interpolate(
    ctaSpring,
    [0, 1],
    [0.8, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const ctaOpacity = interpolate(
    frame,
    [80, 100],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Animated particles
  const particles = Array.from({ length: 20 }, (_, i) => {
    const particleDelay = i * 5;
    const particleProgress = interpolate(
      frame,
      [particleDelay, particleDelay + 60],
      [0, 1],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    );

    return {
      x: Math.random() * 1920,
      y: interpolate(particleProgress, [0, 1], [1080, -100]),
      size: 4 + Math.random() * 8,
      opacity: interpolate(particleProgress, [0, 0.2, 0.8, 1], [0, 0.6, 0.6, 0]),
    };
  });

  return (
    <AbsoluteFill
      style={{
        background: '#0A0A0A',
        fontFamily: 'Inter, sans-serif',
        overflow: 'hidden',
      }}
    >
      {/* Animated gradient background */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(ellipse at 50% 50%, #0066FF33 0%, transparent 60%)',
          transform: `scale(${bgScale})`,
        }}
      />

      {/* Animated particles */}
      {particles.map((particle, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: particle.x,
            top: particle.y,
            width: particle.size,
            height: particle.size,
            backgroundColor: '#00D9FF',
            borderRadius: '50%',
            opacity: particle.opacity,
            boxShadow: '0 0 10px #00D9FF',
          }}
        />
      ))}

      {/* Grid pattern overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(0, 102, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 102, 255, 0.03) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />

      {/* Content */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          textAlign: 'center',
          padding: '0 160px',
        }}
      >
        {/* Headline */}
        <h1
          style={{
            fontSize: 96,
            fontWeight: 700,
            color: '#FFFFFF',
            margin: 0,
            marginBottom: 32,
            fontFamily: 'Clash Display, sans-serif',
            transform: `translateY(${headlineY}px)`,
            opacity: headlineOpacity,
            lineHeight: 1.1,
            letterSpacing: '-0.02em',
          }}
        >
          {headline}
        </h1>

        {/* Subheadline */}
        <p
          style={{
            fontSize: 36,
            color: 'rgba(255, 255, 255, 0.7)',
            margin: 0,
            marginBottom: 60,
            maxWidth: 900,
            transform: `translateY(${subY}px)`,
            opacity: subOpacity,
            lineHeight: 1.4,
          }}
        >
          {subheadline}
        </p>

        {/* CTA Button */}
        <div
          style={{
            transform: `scale(${ctaScale})`,
            opacity: ctaOpacity,
          }}
        >
          <div
            style={{
              background: 'linear-gradient(135deg, #0066FF 0%, #00D9FF 100%)',
              padding: '24px 60px',
              borderRadius: 16,
              fontSize: 28,
              fontWeight: 600,
              color: '#FFFFFF',
              boxShadow: '0 20px 40px rgba(0, 102, 255, 0.4)',
            }}
          >
            {cta}
          </div>
        </div>
      </div>

      {/* Velocity indicator decoration */}
      <div
        style={{
          position: 'absolute',
          bottom: 80,
          left: 80,
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          opacity: interpolate(
            frame,
            [120, 140],
            [0, 1],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          ),
        }}
      >
        <div
          style={{
            width: 60,
            height: 6,
            background: 'linear-gradient(90deg, #00C853, #00D9FF)',
            borderRadius: 3,
          }}
        />
        <span
          style={{
            fontSize: 18,
            color: '#00C853',
            fontWeight: 600,
          }}
        >
          Live Trend Detection
        </span>
      </div>

      {/* Brand Logo */}
      <div
        style={{
          position: 'absolute',
          top: 48,
          left: 80,
          fontSize: 28,
          fontWeight: 700,
          color: '#FFFFFF',
          fontFamily: 'Clash Display, sans-serif',
        }}
      >
        Trendscope
      </div>

      {/* Stats decoration */}
      <div
        style={{
          position: 'absolute',
          top: 48,
          right: 80,
          display: 'flex',
          gap: 32,
          opacity: interpolate(
            frame,
            [100, 120],
            [0, 1],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          ),
        }}
      >
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#FFFFFF' }}>2.4M+</div>
          <div style={{ fontSize: 14, color: '#6B7280' }}>Trends Analyzed</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#00D9FF' }}>99.9%</div>
          <div style={{ fontSize: 14, color: '#6B7280' }}>Accuracy</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
