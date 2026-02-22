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
  spring,
} from 'remotion';
import { OrbitalRingsEnhanced } from '../components/option-a/OrbitalRingsEnhanced';
import { CurvedSweepLines } from '../components/option-a/CurvedSweepLines';
import { ParticleField } from '../components/option-a/ParticleField';
import { WireframeGlobe2D } from '../components/option-a/WireframeGlobe2D';

// Color palette from the plan
const COLORS = {
  bgDark: '#020617',
  bgCard: '#0F172A',
  accentCyan: '#00D9FF',
  accentBlue: '#3B82F6',
  accentOrange: '#F59E0B',
  accentTeal: '#14B8A6',
  success: '#10B981',
  white: '#FFFFFF',
  white70: 'rgba(255,255,255,0.7)',
};

interface BloombergIntroProps {
  logoUrl?: string;
  montageImages?: string[];
  globeUrl?: string;
}

// Scene 1: Enhanced Logo Reveal with glow effects and spring animations
const Scene1LogoReveal: React.FC<{ logoUrl: string }> = ({ logoUrl }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Logo fade in and scale with spring animation
  const logoSpring = spring({
    frame: frame - 30,
    fps,
    config: { damping: 15, stiffness: 100 },
    durationInFrames: 40,
  });

  const logoOpacity = interpolate(
    logoSpring,
    [0, 1],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const logoScale = interpolate(
    logoSpring,
    [0, 1],
    [0.8, 1.0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Fade out at end of scene (frames 200-240 of the 240-frame scene)
  const exitProgress = interpolate(
    frame,
    [200, 240],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Text reveal with spring
  const textSpring = spring({
    frame: frame - 50,
    fps,
    config: { damping: 20, stiffness: 150 },
    durationInFrames: 35,
  });

  const textOpacity = interpolate(
    textSpring,
    [0, 1],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const textY = interpolate(
    textSpring,
    [0, 1],
    [30, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Letter spacing animation
  const letterSpacing = interpolate(
    frame,
    [50, 85],
    [0.3, 0.15],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

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
      {/* Background gradient with subtle animation */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(ellipse at 50% 50%, rgba(0, 217, 255, ${0.08 + Math.sin(frame * 0.05) * 0.04}) 0%, transparent 70%)`,
        }}
      />

      {/* Enhanced orbital rings with glow and gradient */}
      <OrbitalRingsEnhanced />

      {/* Curved sweep lines with motion blur */}
      <CurvedSweepLines />

      {/* Particle field with depth layers */}
      <ParticleField particleCount={60} />

      {/* Logo with spring animation and glow */}
      <div
        style={{
          position: 'absolute',
          opacity: logoOpacity * exitProgress,
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
            width: 1000,
            height: 'auto',
            filter: 'drop-shadow(0 0 40px rgba(255,255,255,0.3)) drop-shadow(0 0 80px rgba(0, 217, 255, 0.2))',
          }}
        />
      </div>

      {/* Tagline with gradient text and glow */}
      <div
        style={{
          position: 'absolute',
          bottom: 280,
          opacity: textOpacity * exitProgress,
          transform: `translateY(${textY}px)`,
        }}
      >
        <p
          style={{
            fontSize: 56,
            color: COLORS.white70,
            letterSpacing: `${letterSpacing}em`,
            textTransform: 'uppercase',
            fontFamily: 'Inter, system-ui, sans-serif',
            textAlign: 'center',
            fontWeight: 600,
            textShadow: '0 0 40px rgba(0, 217, 255, 0.5)',
          }}
        >
          The Bloomberg Terminal for Short-Form Video Trends
        </p>
      </div>
    </AbsoluteFill>
  );
};

// Scene 2: Sliding Tile Montage with Ken Burns effect
const Scene2Montage: React.FC<{ images: string[] }> = ({ images }) => {
  const frame = useCurrentFrame();
  const localFrame = frame - 240; // Adjust for sequence start (DOUBLED)

  // Marketing-aligned text
  const montageData = [
    {
      text: 'DETECT EARLY',
      subtext: 'Catch trends at the micro-influencer layer',
      image: images[0] || '',
    },
    {
      text: 'TRACK VELOCITY',
      subtext: 'Monitor growth rate, not just volume',
      image: images[1] || '',
    },
    {
      text: 'BEAT THE DECAY',
      subtext: 'Act while the window is still open',
      image: images[2] || '',
    },
    {
      text: 'CREATE FIRST',
      subtext: 'Post before the mainstream knows',
      image: images[3] || '',
    },
  ];

  // Scene timing: Each scene displays for 180 frames (6 seconds) with 60-frame transitions (DOUBLED)
  const sceneDuration = 180;
  const transitionDuration = 60;
  const totalCycle = sceneDuration + transitionDuration;

  const getSceneInfo = (frameNum: number) => {
    for (let i = 0; i < montageData.length; i++) {
      const startFrame = i * sceneDuration;
      const endFrame = startFrame + totalCycle;
      
      if (frameNum >= startFrame && frameNum < endFrame) {
        const isTransition = frameNum >= startFrame + sceneDuration - transitionDuration && i < montageData.length - 1;
        return {
          index: i,
          progress: frameNum - startFrame,
          isTransition,
          nextIndex: isTransition ? i + 1 : i,
        };
      }
    }
    // Last scene holds without transition
    const lastStart = (montageData.length - 1) * sceneDuration;
    return {
      index: montageData.length - 1,
      progress: Math.min(frameNum - lastStart, sceneDuration - 1),
      isTransition: false,
      nextIndex: montageData.length - 1,
    };
  };

  const { index: sceneIndex, progress: sceneProgress, isTransition, nextIndex } = getSceneInfo(localFrame);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bgDark,
        overflow: 'hidden',
      }}
    >
      {montageData.map((scene, index) => {
        const isActive = index === sceneIndex;
        const isNext = index === nextIndex && isTransition;
        const hasPassed = index < sceneIndex;

        // Calculate visibility
        let opacity = 0;
        let translateX = 0;
        let imageScale = 1;
        let imageTranslateX = 0;

        if (isActive) {
          // Fade in quickly, hold, fade out during transition
          if (sceneProgress < 30) {
            opacity = interpolate(sceneProgress, [0, 30], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
            translateX = interpolate(sceneProgress, [0, 30], [index % 2 === 0 ? 1920 : -1920, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
          } else if (sceneProgress >= sceneDuration - transitionDuration && isTransition) {
            // During transition to next scene
            const transitionProgress = sceneProgress - (sceneDuration - transitionDuration);
            opacity = interpolate(transitionProgress, [0, 30], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
            translateX = interpolate(transitionProgress, [0, 60], [0, index % 2 === 0 ? -1920 : 1920], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.cubic) });
          } else {
            opacity = 1;
            translateX = 0;
          }

          // Ken Burns effect - subtle zoom and pan
          const kenBurnsProgress = Math.min(sceneProgress, sceneDuration - transitionDuration);
          imageScale = interpolate(kenBurnsProgress, [0, sceneDuration - transitionDuration], [1, 1.08], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          imageTranslateX = interpolate(kenBurnsProgress, [0, sceneDuration - transitionDuration], [0, index % 2 === 0 ? 20 : -20], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        } else if (isNext && isTransition) {
          const transitionProgress = sceneProgress - (sceneDuration - transitionDuration);
          opacity = interpolate(transitionProgress, [0, 40], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          translateX = interpolate(transitionProgress, [0, 60], [index % 2 === 0 ? 1920 : -1920, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
        } else if (hasPassed) {
          opacity = 0;
        }

        // Text animations (DOUBLED delays)
        const textDelay = 30;
        const textFadeOutStart = sceneDuration - 60;
        const textFadeOutEnd = sceneDuration - 30;

        const textOpacity = isActive ? interpolate(
          sceneProgress,
          [textDelay, textDelay + 20, textFadeOutStart, textFadeOutEnd],
          [0, 1, 1, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        ) : 0;

        const textY = isActive ? interpolate(
          sceneProgress,
          [textDelay, textDelay + 20],
          [60, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
        ) : 0;

        const subtextDelay = 60;
        const subtextOpacity = isActive ? interpolate(
          sceneProgress,
          [subtextDelay, subtextDelay + 20, textFadeOutStart, textFadeOutEnd],
          [0, 1, 1, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        ) : 0;

        const subtextY = isActive ? interpolate(
          sceneProgress,
          [subtextDelay, subtextDelay + 20],
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
            {/* Background image with Ken Burns effect */}
            <div
              style={{
                position: 'absolute',
                inset: 0,
                overflow: 'hidden',
              }}
            >
              <Img
                src={staticFile(scene.image)}
                style={{
                  position: 'absolute',
                  width: '110%',
                  height: '110%',
                  objectFit: 'cover',
                  objectPosition: 'center',
                  transform: `scale(${imageScale}) translateX(${imageTranslateX}px)`,
                  transformOrigin: 'center center',
                }}
              />
            </div>

            {/* Dark overlay with gradient */}
            <div
              style={{
                position: 'absolute',
                inset: 0,
                background: 'linear-gradient(90deg, rgba(2, 6, 23, 0.95) 0%, rgba(2, 6, 23, 0.6) 50%, rgba(2, 6, 23, 0.95) 100%)',
              }}
            />

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
              {/* Main Text with gradient and glow */}
              <h2
                style={{
                  fontSize: 100,
                  fontWeight: 800,
                  color: COLORS.white,
                  letterSpacing: '-0.02em',
                  textTransform: 'uppercase',
                  transform: `translateY(${textY}px)`,
                  opacity: textOpacity,
                  textShadow: `0 0 80px ${COLORS.accentCyan}60`,
                  fontFamily: 'Inter, system-ui, sans-serif',
                  margin: 0,
                  marginBottom: 24,
                  background: 'linear-gradient(135deg, #FFFFFF 0%, #00D9FF 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                }}
              >
                {scene.text}
              </h2>

              {/* Subtext */}
              <p
                style={{
                  fontSize: 36,
                  color: COLORS.white70,
                  letterSpacing: '0.02em',
                  fontFamily: 'Inter, system-ui, sans-serif',
                  transform: `translateY(${subtextY}px)`,
                  opacity: subtextOpacity,
                  maxWidth: 900,
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

// Scene 3: Title Reveal with wireframe globe and trajectory arcs
const Scene3TitleReveal: React.FC<{ globeUrl: string }> = ({ globeUrl }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = frame;

  // Background fade in
  const bgOpacity = interpolate(
    localFrame,
    [0, 20],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Title spring animation
  const titleSpring = spring({
    frame: localFrame - 20,
    fps,
    config: { damping: 15, stiffness: 100 },
    durationInFrames: 40,
  });

  const titleOpacity = interpolate(
    titleSpring,
    [0, 1],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const titleX = interpolate(
    titleSpring,
    [0, 1],
    [100, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Tagline animation
  const taglineSpring = spring({
    frame: localFrame - 50,
    fps,
    config: { damping: 20, stiffness: 120 },
    durationInFrames: 35,
  });

  const taglineOpacity = interpolate(
    taglineSpring,
    [0, 1],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const taglineY = interpolate(
    taglineSpring,
    [0, 1],
    [40, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // CTA animation
  const ctaSpring = spring({
    frame: localFrame - 90,
    fps,
    config: { damping: 20, stiffness: 150 },
    durationInFrames: 30,
  });

  const ctaOpacity = interpolate(
    ctaSpring,
    [0, 1],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Decorative line animation
  const lineWidth = interpolate(
    localFrame,
    [80, 130],
    [0, 240],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
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

      {/* Digital Globe with 3D rotation and trajectory arcs */}
      <div
        style={{
          position: 'absolute',
          left: 80,
          top: '50%',
          transform: 'translateY(-50%)',
        }}
      >
        <WireframeGlobe2D globeUrl={globeUrl} />
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
        {/* Main Title with gradient */}
        <h1
          style={{
            fontSize: 120,
            fontWeight: 800,
            margin: 0,
            marginBottom: 28,
            letterSpacing: '-0.02em',
            fontFamily: 'Inter, system-ui, sans-serif',
            opacity: titleOpacity,
            transform: `translateX(${titleX}px)`,
            background: 'linear-gradient(135deg, #FFFFFF 0%, #00D9FF 50%, #3B82F6 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            filter: 'drop-shadow(0 0 40px rgba(0, 217, 255, 0.3))',
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
            marginBottom: 40,
            letterSpacing: '0.02em',
            fontFamily: 'Inter, system-ui, sans-serif',
            opacity: taglineOpacity,
            transform: `translateY(${taglineY}px)`,
            lineHeight: 1.5,
          }}
        >
          Real-time trend intelligence.<br />
          Alerts 6-24 hours before the mainstream knows.
        </p>

        {/* Decorative line */}
        <div
          style={{
            height: 4,
            width: lineWidth,
            background: `linear-gradient(90deg, ${COLORS.accentCyan}, ${COLORS.accentBlue})`,
            borderRadius: 2,
            marginBottom: 40,
            boxShadow: `0 0 20px ${COLORS.accentCyan}60`,
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
              padding: '24px 56px',
              borderRadius: 12,
              fontSize: 26,
              fontWeight: 600,
              color: COLORS.white,
              boxShadow: `0 15px 35px rgba(0, 102, 255, 0.4), 0 0 30px rgba(0, 217, 255, 0.3)`,
              fontFamily: 'Inter, system-ui, sans-serif',
              letterSpacing: '0.05em',
              textTransform: 'uppercase',
            }}
          >
            START FREE TRIAL →
          </div>
          <p
            style={{
              fontSize: 18,
              color: COLORS.white70,
              marginTop: 20,
              fontFamily: 'Inter, system-ui, sans-serif',
            }}
          >
            14 days free • No credit card required
          </p>
        </div>
      </div>

      {/* Bottom accent particles with staggered animation */}
      {Array.from({ length: 12 }).map((_, i) => {
        const particleDelay = i * 4;
        const particleOpacity = interpolate(
          localFrame,
          [particleDelay, particleDelay + 25],
          [0, 0.6],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              bottom: 40 + (i % 3) * 40,
              left: 60 + i * 155,
              width: 4 + (i % 3) * 3,
              height: 4 + (i % 3) * 3,
              backgroundColor: i % 2 === 0 ? COLORS.accentCyan : COLORS.accentBlue,
              borderRadius: '50%',
              opacity: particleOpacity,
              boxShadow: `0 0 ${10 + (i % 3) * 5}px ${i % 2 === 0 ? COLORS.accentCyan : COLORS.accentBlue}`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// Main Composition - Version 10 (DOUBLED DURATIONS)
// Same as V9 but with all scene durations doubled for better readability
export const BloombergIntroV10: React.FC<BloombergIntroProps> = ({
  logoUrl = 'assets/scene1/trendscope-logo-transparent.png',
  montageImages = [
    'assets/scene2/creator-filming-enhanced.jpg',
    'assets/scene2/data-dashboard-enhanced.jpg',
    'assets/scene2/viral-explosion-enhanced.jpg',
    'assets/scene2/phone-alert-enhanced.jpg',
  ],
  globeUrl = 'assets/scene3/wireframe-globe-enhanced.jpg',
}) => {
  return (
    <>
      {/* Scene 1: Enhanced Logo Reveal (0:00 - 0:08 | Frames 0-240) - DOUBLED */}
      <Sequence from={0} durationInFrames={240}>
        <Scene1LogoReveal logoUrl={logoUrl} />
      </Sequence>

      {/* Scene 2: Sliding Tile Montage (0:08 - 0:40 | Frames 240-1200) - DOUBLED */}
      {/* 4 scenes x 180 frames + 3 transitions x 60 frames = 900 frames */}
      <Sequence from={240} durationInFrames={960}>
        <Scene2Montage images={montageImages} />
      </Sequence>

      {/* Scene 3: Title Reveal with Wireframe Globe (0:40 - 0:52 | Frames 1200-1560) - DOUBLED */}
      <Sequence from={1200} durationInFrames={360}>
        <Scene3TitleReveal globeUrl={globeUrl} />
      </Sequence>
    </>
  );
};
