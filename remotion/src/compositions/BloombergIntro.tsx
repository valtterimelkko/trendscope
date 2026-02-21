import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  Sequence,
  Img,
  staticFile,
} from 'remotion';

// Color palette from the plan
const COLORS = {
  bgDark: '#020617',
  bgCard: '#0F172A',
  accentCyan: '#00D9FF',
  accentBlue: '#3B82F6',
  accentOrange: '#F59E0B',
  success: '#10B981',
  white: '#FFFFFF',
  white70: 'rgba(255,255,255,0.7)',
};

interface BloombergIntroProps {
  logoUrl?: string;
  montageImages?: string[];
  globeUrl?: string;
}

// Scene 1: Logo Reveal (0:00 - 0:03 | Frames 0-90)
const Scene1LogoReveal: React.FC<{ logoUrl: string }> = ({ logoUrl }) => {
  const frame = useCurrentFrame();

  // Ring 1 (Left, Cyan) - Rotates clockwise
  const ring1Rotation = interpolate(
    frame,
    [0, 90],
    [0, 180],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Ring 2 (Right, Blue) - Rotates counter-clockwise
  const ring2Rotation = interpolate(
    frame,
    [0, 90],
    [0, -180],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Logo fade in and scale
  const logoOpacity = interpolate(
    frame,
    [45, 75],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const logoScale = interpolate(
    frame,
    [45, 75],
    [0.9, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Sweep lines progress
  const sweepLines = Array.from({ length: 3 }, (_, i) => {
    const delay = i * 15;
    return {
      progress: interpolate(
        frame,
        [delay, delay + 45],
        [-200, 2120],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
      ),
      opacity: interpolate(
        frame,
        [delay, delay + 10, delay + 35, delay + 45],
        [0, 0.8, 0.8, 0],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
      ),
    };
  });

  // Particles
  const particles = Array.from({ length: 30 }, (_, i) => {
    const startDelay = i * 2;
    const x = 200 + (i % 6) * 300 + Math.random() * 100;
    return {
      x,
      y: interpolate(
        frame,
        [startDelay, startDelay + 90],
        [1100, -100],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
      ),
      size: 2 + Math.random() * 4,
      opacity: interpolate(
        frame,
        [startDelay, startDelay + 20, startDelay + 60, startDelay + 90],
        [0, 0.8, 0.8, 0],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
      ),
    };
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bgDark,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        overflow: 'hidden',
      }}
    >
      {/* Background gradient */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(ellipse at 50% 50%, rgba(0, 217, 255, 0.1) 0%, transparent 70%)',
        }}
      />

      {/* Orbital Ring 1 (Cyan, Left) */}
      <div
        style={{
          position: 'absolute',
          width: 600,
          height: 600,
          left: 150,
          top: 240,
          border: `3px solid ${COLORS.accentCyan}`,
          borderRadius: '50%',
          opacity: 0.6,
          transform: `rotate(${ring1Rotation}deg)`,
          boxShadow: `0 0 30px ${COLORS.accentCyan}40`,
        }}
      />

      {/* Orbital Ring 2 (Blue, Right) */}
      <div
        style={{
          position: 'absolute',
          width: 500,
          height: 500,
          right: 200,
          top: 290,
          border: `3px solid ${COLORS.accentBlue}`,
          borderRadius: '50%',
          opacity: 0.5,
          transform: `rotate(${ring2Rotation}deg)`,
          boxShadow: `0 0 30px ${COLORS.accentBlue}40`,
        }}
      />

      {/* Sweep lines */}
      {sweepLines.map((line, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: line.progress,
            top: 200 + i * 250,
            width: 200,
            height: 2,
            background: `linear-gradient(90deg, transparent, ${COLORS.accentCyan}, transparent)`,
            opacity: line.opacity,
            transform: 'rotate(-15deg)',
          }}
        />
      ))}

      {/* Particles */}
      {particles.map((particle, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: particle.x,
            top: particle.y,
            width: particle.size,
            height: particle.size,
            backgroundColor: COLORS.accentCyan,
            borderRadius: '50%',
            opacity: particle.opacity,
            boxShadow: `0 0 8px ${COLORS.accentCyan}`,
          }}
        />
      ))}

      {/* Logo */}
      <div
        style={{
          position: 'absolute',
          opacity: logoOpacity,
          transform: `scale(${logoScale})`,
          zIndex: 10,
        }}
      >
        <Img
          src={staticFile(logoUrl)}
          style={{
            width: 500,
            height: 'auto',
            filter: 'drop-shadow(0 0 40px rgba(255,255,255,0.3))',
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

// Scene 2: Montage (0:03 - 0:11 | Frames 90-330)
const Scene2Montage: React.FC<{ images: string[] }> = ({ images }) => {
  const frame = useCurrentFrame();
  const localFrame = frame - 90; // Adjust for sequence start

  const montageData = [
    { text: 'DETECTING SIGNALS', image: images[0] || '' },
    { text: 'FOLLOWING VELOCITY', image: images[1] || '' },
    { text: 'WINDOW OPENING', image: images[2] || '' },
    { text: 'ACT FIRST', image: images[3] || '' },
  ];

  // Determine current scene (each lasts 60 frames)
  const sceneIndex = Math.min(Math.floor(localFrame / 60), 3);
  const sceneProgress = localFrame % 60;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bgDark,
        overflow: 'hidden',
      }}
    >
      {montageData.map((scene, index) => {
        const isActive = index === sceneIndex;
        const hasPassed = index < sceneIndex;
        
        // Calculate visibility and position
        let opacity = 0;
        let translateX = 0;
        
        if (isActive) {
          opacity = interpolate(
            sceneProgress,
            [0, 15, 45, 60],
            [0, 1, 1, 0],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          );
          translateX = interpolate(
            sceneProgress,
            [0, 20],
            index % 2 === 0 ? [1920, 0] : [-1920, 0],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.quad) }
          );
        } else if (hasPassed) {
          opacity = 0;
        }

        // Text animation
        const textOpacity = isActive ? interpolate(
          sceneProgress,
          [10, 30, 45, 60],
          [0, 1, 1, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        ) : 0;

        const textY = isActive ? interpolate(
          sceneProgress,
          [10, 30],
          [100, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.ease) }
        ) : 0;

        return (
          <div
            key={index}
            style={{
              position: 'absolute',
              inset: 0,
              opacity,
              transform: `translateX(${translateX}px)`,
            }}
          >
            {/* Background image with overlay */}
            <div
              style={{
                position: 'absolute',
                inset: 0,
                backgroundImage: `url(${staticFile(scene.image)})`,
                backgroundSize: 'cover',
                backgroundPosition: 'center',
              }}
            >
              {/* Dark overlay */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  background: 'linear-gradient(90deg, rgba(2, 6, 23, 0.9) 0%, rgba(2, 6, 23, 0.4) 50%, rgba(2, 6, 23, 0.9) 100%)',
                }}
              />
            </div>

            {/* Text overlay */}
            <div
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                opacity: textOpacity,
              }}
            >
              <h2
                style={{
                  fontSize: 80,
                  fontWeight: 800,
                  color: COLORS.white,
                  letterSpacing: '-0.02em',
                  textTransform: 'uppercase',
                  transform: `translateY(${textY}px)`,
                  textShadow: `0 0 60px ${COLORS.accentCyan}60`,
                  fontFamily: 'Inter, system-ui, sans-serif',
                }}
              >
                {scene.text}
              </h2>
            </div>
          </div>
        );
      })}

      {/* Sliding strips effect overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
        }}
      >
        {Array.from({ length: 5 }).map((_, i) => {
          const stripDelay = i * 3;
          const stripOpacity = interpolate(
            localFrame,
            [stripDelay, stripDelay + 10],
            [0.3, 0],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          );
          
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: 0,
                right: 0,
                top: `${i * 20}%`,
                height: '20%',
                backgroundColor: COLORS.accentCyan,
                opacity: stripOpacity,
                transform: `translateX(${i % 2 === 0 ? -100 : 100}%)`,
              }}
            />
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// Scene 3: Title Reveal (0:11 - 0:15 | Frames 330-450)
const Scene3TitleReveal: React.FC<{ globeUrl: string }> = ({ globeUrl }) => {
  const frame = useCurrentFrame();
  const localFrame = frame - 330; // Adjust for sequence start

  // Background fade in
  const bgOpacity = interpolate(
    localFrame,
    [0, 15],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Title animation
  const titleProgress = interpolate(
    localFrame,
    [30, 70],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  const titleOpacity = interpolate(
    localFrame,
    [30, 50],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const titleX = interpolate(
    localFrame,
    [30, 70],
    [100, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Tagline animation
  const taglineOpacity = interpolate(
    localFrame,
    [70, 90],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const taglineY = interpolate(
    localFrame,
    [70, 90],
    [20, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Trajectory lines
  const trajectoryLines = Array.from({ length: 5 }, (_, i) => {
    const startDelay = 15 + i * 10;
    return {
      length: interpolate(
        localFrame,
        [startDelay, startDelay + 45],
        [0, 1],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
      ),
      opacity: interpolate(
        localFrame,
        [startDelay, startDelay + 15, startDelay + 35, startDelay + 45],
        [0, 1, 1, 0.7],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
      ),
      color: i % 2 === 0 ? COLORS.accentOrange : COLORS.accentCyan,
      angle: i * 72,
    };
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bgCard,
        opacity: bgOpacity,
        overflow: 'hidden',
      }}
    >
      {/* Background grid */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(0, 217, 255, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 217, 255, 0.05) 1px, transparent 1px)
          `,
          backgroundSize: '80px 80px',
        }}
      />

      {/* Digital Globe (Left side) */}
      <div
        style={{
          position: 'absolute',
          left: 150,
          top: '50%',
          transform: 'translateY(-50%)',
          width: 600,
          height: 600,
        }}
      >
        <Img
          src={staticFile(globeUrl)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            opacity: interpolate(
              localFrame,
              [0, 30],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            ),
          }}
        />

        {/* Trajectory arcs overlay */}
        {trajectoryLines.map((line, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              width: 400 + i * 50,
              height: 400 + i * 50,
              border: `2px solid ${line.color}`,
              borderRadius: '50%',
              borderLeftColor: 'transparent',
              borderBottomColor: 'transparent',
              transform: `translate(-50%, -50%) rotate(${line.angle + localFrame * 0.5}deg)`,
              opacity: line.opacity * 0.6,
              boxShadow: `0 0 20px ${line.color}40`,
            }}
          />
        ))}
      </div>

      {/* Title and Tagline (Right side) */}
      <div
        style={{
          position: 'absolute',
          right: 150,
          top: '50%',
          transform: 'translateY(-50%)',
          textAlign: 'left',
          maxWidth: 900,
        }}
      >
        {/* Main Title */}
        <h1
          style={{
            fontSize: 120,
            fontWeight: 800,
            color: COLORS.white,
            margin: 0,
            marginBottom: 24,
            letterSpacing: '-0.02em',
            fontFamily: 'Inter, system-ui, sans-serif',
            opacity: titleOpacity,
            transform: `translateX(${titleX}px)`,
            textShadow: `0 0 60px ${COLORS.accentCyan}40`,
          }}
        >
          TRENDSCOPE
        </h1>

        {/* Tagline */}
        <p
          style={{
            fontSize: 32,
            color: COLORS.white70,
            margin: 0,
            letterSpacing: '0.02em',
            fontFamily: 'Inter, system-ui, sans-serif',
            opacity: taglineOpacity,
            transform: `translateY(${taglineY}px)`,
          }}
        >
          The Bloomberg Terminal of Short-Form Video Trends
        </p>

        {/* Decorative line */}
        <div
          style={{
            marginTop: 40,
            height: 4,
            width: interpolate(
              localFrame,
              [90, 120],
              [0, 200],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
            ),
            background: `linear-gradient(90deg, ${COLORS.accentCyan}, ${COLORS.accentBlue})`,
            borderRadius: 2,
          }}
        />
      </div>

      {/* Bottom accent particles */}
      {Array.from({ length: 10 }).map((_, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            bottom: 40 + Math.random() * 100,
            left: 100 + i * 180,
            width: 4 + Math.random() * 4,
            height: 4 + Math.random() * 4,
            backgroundColor: COLORS.accentCyan,
            borderRadius: '50%',
            opacity: interpolate(
              localFrame,
              [i * 5, i * 5 + 20],
              [0, 0.6],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            ),
            boxShadow: `0 0 10px ${COLORS.accentCyan}`,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

// Main Composition
export const BloombergIntro: React.FC<BloombergIntroProps> = ({
  logoUrl = 'assets/scene1/trendscope-logo-white.png',
  montageImages = [
    'assets/scene2/creator-filming.jpg',
    'assets/scene2/data-dashboard.jpg',
    'assets/scene2/viral-explosion.jpg',
    'assets/scene2/alert-phone.jpg',
  ],
  globeUrl = 'assets/scene3/digital-globe.jpg',
}) => {
  return (
    <>
      {/* Scene 1: Logo Reveal (0:00 - 0:03 | Frames 0-90) */}
      <Sequence from={0} durationInFrames={90}>
        <Scene1LogoReveal logoUrl={logoUrl} />
      </Sequence>

      {/* Scene 2: Montage (0:03 - 0:11 | Frames 90-330) */}
      <Sequence from={90} durationInFrames={240}>
        <Scene2Montage images={montageImages} />
      </Sequence>

      {/* Scene 3: Title Reveal (0:11 - 0:15 | Frames 330-450) */}
      <Sequence from={330} durationInFrames={120}>
        <Scene3TitleReveal globeUrl={globeUrl} />
      </Sequence>
    </>
  );
};
