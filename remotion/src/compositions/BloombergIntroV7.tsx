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

// Scene 1: Logo Reveal (0:00 - 0:06 | Frames 0-180)
// Extended to 180 frames (6 seconds) - 1.5x longer than before
// V7: Using new high-quality logo at 500px width (same as V6)
const Scene1LogoReveal: React.FC<{ logoUrl: string }> = ({ logoUrl }) => {
  const frame = useCurrentFrame();

  // Ring 1 (Left, Cyan) - Rotates clockwise
  const ring1Rotation = interpolate(
    frame,
    [0, 180],
    [0, 360],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Ring 2 (Right, Blue) - Rotates counter-clockwise
  const ring2Rotation = interpolate(
    frame,
    [0, 180],
    [0, -360],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Logo fade in and scale
  // Adjusted timing for longer scene
  const logoOpacity = interpolate(
    frame,
    [30, 70],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const logoScale = interpolate(
    frame,
    [30, 70],
    [0.85, 1.0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );
  
  // Fade out at end of scene (frames 150-180)
  const exitOpacity = interpolate(
    frame,
    [150, 170],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Sweep lines progress
  const sweepLines = Array.from({ length: 4 }, (_, i) => {
    const delay = i * 12;
    return {
      progress: interpolate(
        frame,
        [delay, delay + 50],
        [-200, 2120],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
      ),
      opacity: interpolate(
        frame,
        [delay, delay + 10, delay + 40, delay + 50],
        [0, 0.8, 0.8, 0],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
      ),
    };
  });

  // Particles
  const particles = Array.from({ length: 40 }, (_, i) => {
    const startDelay = i * 2;
    const x = 150 + (i % 8) * 250 + Math.random() * 100;
    return {
      x,
      y: interpolate(
        frame,
        [startDelay, startDelay + 120],
        [1100, -100],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
      ),
      size: 2 + Math.random() * 5,
      opacity: interpolate(
        frame,
        [startDelay, startDelay + 20, startDelay + 80, startDelay + 120],
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
          background: 'radial-gradient(ellipse at 50% 50%, rgba(0, 217, 255, 0.12) 0%, transparent 70%)',
        }}
      />

      {/* Orbital Ring 1 (Cyan, Left) */}
      <div
        style={{
          position: 'absolute',
          width: 700,
          height: 700,
          left: 100,
          top: 190,
          border: `3px solid ${COLORS.accentCyan}`,
          borderRadius: '50%',
          opacity: 0.5,
          transform: `rotate(${ring1Rotation}deg)`,
          boxShadow: `0 0 40px ${COLORS.accentCyan}40`,
        }}
      />

      {/* Orbital Ring 2 (Blue, Right) */}
      <div
        style={{
          position: 'absolute',
          width: 600,
          height: 600,
          right: 150,
          top: 240,
          border: `3px solid ${COLORS.accentBlue}`,
          borderRadius: '50%',
          opacity: 0.4,
          transform: `rotate(${ring2Rotation}deg)`,
          boxShadow: `0 0 40px ${COLORS.accentBlue}40`,
        }}
      />

      {/* Sweep lines */}
      {sweepLines.map((line, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: line.progress,
            top: 150 + i * 220,
            width: 250,
            height: 2,
            background: `linear-gradient(90deg, transparent, ${COLORS.accentCyan}, transparent)`,
            opacity: line.opacity,
            transform: 'rotate(-12deg)',
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
            boxShadow: `0 0 10px ${COLORS.accentCyan}`,
          }}
        />
      ))}

      {/* Logo - V7: Using new high-quality logo at 500px (same size as V6) */}
      <div
        style={{
          position: 'absolute',
          opacity: logoOpacity * exitOpacity,
          transform: `scale(${logoScale})`,
          zIndex: 10,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
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

      {/* Tagline below logo */}
      <div
        style={{
          position: 'absolute',
          bottom: 280,
          opacity: interpolate(
            frame,
            [70, 100],
            [0, 1],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          ) * exitOpacity,
          transform: `translateY(${interpolate(
            frame,
            [70, 100],
            [30, 0],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          )}px)`,
        }}
      >
        <p
          style={{
            fontSize: 56,
            color: COLORS.white70,
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            fontFamily: 'Inter, system-ui, sans-serif',
            textAlign: 'center',
            fontWeight: 600,
          }}
        >
          The Bloomberg Terminal for Short-Form Video Trends
        </p>
      </div>
    </AbsoluteFill>
  );
};

// Scene 2: Montage (0:06 - 0:32 | Frames 180-960)
// Scene 1-2 transition: CUT - no black gap (starts immediately at frame 180)
// Last scene (CREATE FIRST) DOUBLED: 300 frames (10s) instead of 150 (5s)
const Scene2Montage: React.FC<{ images: string[] }> = ({ images }) => {
  const frame = useCurrentFrame();
  const localFrame = frame - 180; // Adjust for sequence start (Scene 1 now 180 frames)

  // Marketing-aligned text
  const montageData = [
    { 
      text: 'DETECT EARLY', 
      subtext: 'Catch trends at the micro-influencer layer',
      image: images[0] || '' 
    },
    { 
      text: 'TRACK VELOCITY', 
      subtext: 'Monitor growth rate, not just volume',
      image: images[1] || '' 
    },
    { 
      text: 'BEAT THE DECAY', 
      subtext: 'Act while the window is still open',
      image: images[2] || '' 
    },
    { 
      text: 'CREATE FIRST', 
      subtext: 'Post before the mainstream knows',
      image: images[3] || '' 
    },
  ];

  // Scenes 1-3: 150 frames (5 seconds) each
  // Scene 4 (CREATE FIRST): DOUBLED to 300 frames (10 seconds)
  // Quick transition between scenes: 10 frames (0.33s)
  const getSceneInfo = (frameNum: number) => {
    if (frameNum < 150) return { index: 0, progress: frameNum, totalDuration: 150 };
    if (frameNum < 300) return { index: 1, progress: frameNum - 150, totalDuration: 150 };
    if (frameNum < 450) return { index: 2, progress: frameNum - 300, totalDuration: 150 };
    // Scene 4 (index 3) is DOUBLED - 300 frames
    return { index: 3, progress: Math.min(frameNum - 450, 299), totalDuration: 300 };
  };
  
  const { index: sceneIndex, progress: sceneProgress } = getSceneInfo(localFrame);

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
          // For last scene (index 3), use 300 frames with extended hold
          // For other scenes, use 150 frames
          const totalDuration = index === 3 ? 300 : 150;
          const fadeOutStart = totalDuration - 15;
          const holdEnd = totalDuration - 15;
          
          // Quick transition in (0-10 frames), long hold, fade out at end
          opacity = interpolate(
            sceneProgress,
            [0, 10, holdEnd, totalDuration],
            [0, 1, 1, 0],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          );
          translateX = interpolate(
            sceneProgress,
            [0, 12],
            index % 2 === 0 ? [1920, 0] : [-1920, 0],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.quad) }
          );
        } else if (hasPassed) {
          opacity = 0;
        }

        // Main text animation - adjusted for variable scene length
        const totalDuration = index === 3 ? 300 : 150;
        const textFadeOutStart = totalDuration - 30;
        const textFadeOutEnd = totalDuration - 15;
        
        const textOpacity = isActive ? interpolate(
          sceneProgress,
          [15, 35, textFadeOutStart, textFadeOutEnd],
          [0, 1, 1, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        ) : 0;

        const textY = isActive ? interpolate(
          sceneProgress,
          [15, 35],
          [80, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
        ) : 0;

        // Subtext animation - adjusted for variable scene length
        const subtextFadeOutStart = totalDuration - 30;
        const subtextFadeOutEnd = totalDuration - 15;
        
        const subtextOpacity = isActive ? interpolate(
          sceneProgress,
          [30, 50, subtextFadeOutStart, subtextFadeOutEnd],
          [0, 1, 1, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        ) : 0;

        const subtextY = isActive ? interpolate(
          sceneProgress,
          [30, 50],
          [40, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
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
                  background: 'linear-gradient(90deg, rgba(2, 6, 23, 0.92) 0%, rgba(2, 6, 23, 0.5) 50%, rgba(2, 6, 23, 0.92) 100%)',
                }}
              />
            </div>

            {/* Content container */}
            <div
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                textAlign: 'center',
              }}
            >
              {/* Main Text */}
              <h2
                style={{
                  fontSize: 90,
                  fontWeight: 800,
                  color: COLORS.white,
                  letterSpacing: '-0.02em',
                  textTransform: 'uppercase',
                  transform: `translateY(${textY}px)`,
                  opacity: textOpacity,
                  textShadow: `0 0 80px ${COLORS.accentCyan}60`,
                  fontFamily: 'Inter, system-ui, sans-serif',
                  margin: 0,
                  marginBottom: 20,
                }}
              >
                {scene.text}
              </h2>

              {/* Subtext */}
              <p
                style={{
                  fontSize: 32,
                  color: COLORS.white70,
                  letterSpacing: '0.02em',
                  fontFamily: 'Inter, system-ui, sans-serif',
                  transform: `translateY(${subtextY}px)`,
                  opacity: subtextOpacity,
                  maxWidth: 800,
                  margin: 0,
                }}
              >
                {scene.subtext}
              </p>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// Scene 3: Title Reveal (0:31 - 0:37 | Frames 930-1110)
// Extended to 180 frames (6 seconds) for better readability
// Starts immediately after Scene 2 ends (180 + 150 + 150 + 150 + 300 = 930)
const Scene3TitleReveal: React.FC<{ globeUrl: string }> = ({ globeUrl }) => {
  const frame = useCurrentFrame();
  const localFrame = frame - 930; // Adjust for sequence start

  // Background fade in
  const bgOpacity = interpolate(
    localFrame,
    [0, 20],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Title animation
  const titleOpacity = interpolate(
    localFrame,
    [25, 55],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const titleX = interpolate(
    localFrame,
    [25, 55],
    [80, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Tagline animation
  const taglineOpacity = interpolate(
    localFrame,
    [60, 90],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const taglineY = interpolate(
    localFrame,
    [60, 90],
    [30, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // CTA animation
  const ctaOpacity = interpolate(
    localFrame,
    [110, 140],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

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
          left: 100,
          top: '50%',
          transform: 'translateY(-50%)',
          width: 700,
          height: 700,
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
              [0, 40],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            ),
          }}
        />

        {/* Rotating trajectory arcs */}
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              width: 450 + i * 50,
              height: 450 + i * 50,
              border: `2px solid ${i % 2 === 0 ? COLORS.accentOrange : COLORS.accentCyan}`,
              borderRadius: '50%',
              borderLeftColor: 'transparent',
              borderBottomColor: 'transparent',
              transform: `translate(-50%, -50%) rotate(${i * 72 + localFrame * 0.8}deg)`,
              opacity: 0.5,
              boxShadow: `0 0 20px ${i % 2 === 0 ? COLORS.accentOrange : COLORS.accentCyan}40`,
            }}
          />
        ))}
      </div>

      {/* Title, Tagline and CTA (Right side) */}
      <div
        style={{
          position: 'absolute',
          right: 120,
          top: '50%',
          transform: 'translateY(-50%)',
          textAlign: 'left',
          maxWidth: 950,
        }}
      >
        {/* Main Title */}
        <h1
          style={{
            fontSize: 110,
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
            fontSize: 30,
            color: COLORS.white70,
            margin: 0,
            marginBottom: 40,
            letterSpacing: '0.02em',
            fontFamily: 'Inter, system-ui, sans-serif',
            opacity: taglineOpacity,
            transform: `translateY(${taglineY}px)`,
            lineHeight: 1.4,
          }}
        >
          Real-time trend intelligence.<br />
          Alerts 6-24 hours before the mainstream knows.
        </p>

        {/* Decorative line */}
        <div
          style={{
            height: 4,
            width: interpolate(
              localFrame,
              [100, 140],
              [0, 220],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
            ),
            background: `linear-gradient(90deg, ${COLORS.accentCyan}, ${COLORS.accentBlue})`,
            borderRadius: 2,
            marginBottom: 40,
          }}
        />

        {/* CTA Button */}
        <div
          style={{
            opacity: ctaOpacity,
          }}
        >
          <div
            style={{
              display: 'inline-block',
              background: `linear-gradient(135deg, ${COLORS.accentBlue} 0%, ${COLORS.accentCyan} 100%)`,
              padding: '22px 50px',
              borderRadius: 12,
              fontSize: 24,
              fontWeight: 600,
              color: COLORS.white,
              boxShadow: `0 15px 35px rgba(0, 102, 255, 0.4)`,
              fontFamily: 'Inter, system-ui, sans-serif',
              letterSpacing: '0.05em',
            }}
          >
            START FREE TRIAL →
          </div>
          <p
            style={{
              fontSize: 16,
              color: COLORS.white70,
              marginTop: 16,
              fontFamily: 'Inter, system-ui, sans-serif',
            }}
          >
            14 days free • No credit card required
          </p>
        </div>
      </div>

      {/* Bottom accent particles */}
      {Array.from({ length: 12 }).map((_, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            bottom: 40 + Math.random() * 80,
            left: 80 + i * 150,
            width: 4 + Math.random() * 4,
            height: 4 + Math.random() * 4,
            backgroundColor: COLORS.accentCyan,
            borderRadius: '50%',
            opacity: interpolate(
              localFrame,
              [i * 5, i * 5 + 25],
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

// Main Composition - Version 7
// V7: Uses new high-quality logo from logo/trendscope-logo-transparent.png
// Logo size: 500px width (same as V6)
export const BloombergIntroV7: React.FC<BloombergIntroProps> = ({
  logoUrl = 'assets/scene1/trendscope-logo-transparent.png',
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
      {/* Scene 1: Logo Reveal (0:00 - 0:06 | Frames 0-180) */}
      {/* Extended to 180 frames (6 seconds) - 1.5x longer */}
      <Sequence from={0} durationInFrames={180}>
        <Scene1LogoReveal logoUrl={logoUrl} />
      </Sequence>

      {/* Scene 2: Montage (0:06 - 0:32 | Frames 180-960) */}
      {/* CUT TRANSITION - starts immediately after Scene 1 */}
      {/* 3 scenes x 150 frames + 1 scene x 300 frames = 750 frames */}
      {/* Scene 4 (CREATE FIRST) DOUBLED to 300 frames (10s) */}
      <Sequence from={180} durationInFrames={750}>
        <Scene2Montage images={montageImages} />
      </Sequence>

      {/* Scene 3: Title Reveal (0:31 - 0:37 | Frames 930-1110) */}
      {/* Extended to 180 frames (6 seconds) */}
      <Sequence from={930} durationInFrames={180}>
        <Scene3TitleReveal globeUrl={globeUrl} />
      </Sequence>
    </>
  );
};
