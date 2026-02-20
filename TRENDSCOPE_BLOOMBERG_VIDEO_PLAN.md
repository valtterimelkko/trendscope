# Trendscope "Bloomberg Terminal" Intro Video - Production Plan

> **The Bloomberg Terminal of Short-Form Video Trends**
> 
> A 15-second animated introduction video for the Trendscope landing page

---

## Executive Summary

This document provides a complete blueprint for creating a Bloomberg Brief-style 15-second animated intro video for Trendscope. The video establishes Trendscope as the professional-grade "Bloomberg Terminal" for TikTok and short-form video trend intelligence.

**Target Duration:** 15 seconds (450 frames @ 30fps)  
**Resolution:** 1920x1080 (16:9)  
**Output:** MP4 (H.264) for web playback  
**Audio:** Optional electronic/finance-themed soundtrack

---

## Part 1: Video Blueprint (Agent Implementation Guide)

### Scene Breakdown

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SCENE 1: LOGO REVEAL (0:00 - 0:03)                                         │
│  ├── Dark blue background (#020617)                                         │
│  ├── Two rotating orbital rings (cyan + blue)                               │
│  ├── Sweeping curved data lines                                             │
│  ├── Floating particle effects                                              │
│  └── Trendscope logo fades in center                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  SCENE 2: MONTAGE (0:03 - 0:11)                                             │
│  ├── Sliding tile transition effect                                         │
│  ├── Horizontal strips alternate directions                                 │
│  ├── Scene A: Creator filming ("Detecting Signals")                         │
│  ├── Scene B: Data dashboard ("Following Velocity")                         │
│  ├── Scene C: Viral moment explosion ("Window Opening")                     │
│  └── Scene D: Alert notification ("Act First")                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  SCENE 3: TITLE REVEAL (0:11 - 0:15)                                        │
│  ├── Blue graphical background (#0F172A)                                    │
│  ├── Rotating digital globe with trend lines                                │
│  ├── Orange/cyan trajectory arcs                                            │
│  └── "TRENDSCOPE" title + tagline reveal                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Scene 1: Logo Reveal (0:00 - 0:03 | Frames 0-90)

**Visual Description:**
The video opens on a deep dark blue background (`#020617`). Two large orbital rings begin rotating - one cyan-accented (`#00D9FF`) on the left, one blue-accented (`#3B82F6`) on the right. Thin, curved white lines sweep across the screen. Small cyan particles float upward. The Trendscope logo (text-based) fades into the center within a subtle white/light box.

**Technical Implementation:**

```typescript
// Scene 1: Logo Reveal Component
interface Scene1Props {
  logoUrl: string; // URL to Trendscope logo PNG
}

// Animation timings (frames)
const SCENE1_DURATION = 90; // 3 seconds

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

// Curved sweep lines - multiple staggered
const sweepLines = Array.from({ length: 3 }, (_, i) => ({
  delay: i * 15,
  progress: interpolate(
    frame,
    [i * 15, i * 15 + 45],
    [-200, 2120],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  ),
}));

// Particles - floating upward
const particles = Array.from({ length: 30 }, (_, i) => ({
  x: Math.random() * 1920,
  startY: 1080 + Math.random() * 200,
  size: 2 + Math.random() * 4,
  speed: 0.5 + Math.random() * 1,
  opacity: interpolate(
    frame,
    [0, 30, 60, 90],
    [0, 0.8, 0.8, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  ),
}));

// Logo fade in
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
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
);
```

**Required Assets:**
- `assets/scene1/trendscope-logo-white.png` - White logo on transparent background

---

### Scene 2: Montage (0:03 - 0:11 | Frames 90-330)

**Visual Description:**
Fast-paced montage using a sliding tile effect. Horizontal strips of video/images slide across the screen in alternating directions (left and right), creating a fragmented, dynamic view of the creator economy. Each strip reveals different aspects of trend detection.

**Montage Sequence:**

| Time | Visual | Direction | Text Overlay |
|------|--------|-----------|--------------|
| 0:03-0:05 | Creator filming TikTok content | Strip slides left | "Detecting Signals" |
| 0:05-0:07 | Data dashboard with velocity charts | Strip slides right | "Following Velocity" |
| 0:07-0:09 | Viral video explosion/fire | Strip slides left | "Window Opening" |
| 0:09-0:11 | Alert notification on phone | Strip slides right | "Act First" |

**Technical Implementation:**

```typescript
// Scene 2: Montage Component with Sliding Tiles

// Strip configuration
const STRIP_COUNT = 5;
const STRIP_HEIGHT = 1080 / STRIP_COUNT; // 216px each

// Alternate slide directions per strip
const getStripTransform = (stripIndex: number, frame: number) => {
  const direction = stripIndex % 2 === 0 ? 1 : -1; // Alternate
  const progress = interpolate(
    frame,
    [90 + stripIndex * 5, 150 + stripIndex * 5], // Staggered start
    [direction * 1920, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );
  return progress;
};

// Scene transitions - crossfade between 4 scenes
const sceneIndex = Math.floor((frame - 90) / 60); // 0, 1, 2, 3
const sceneProgress = (frame - 90) % 60;

// Text animations
const textSlide = interpolate(
  sceneProgress,
  [0, 30],
  [100, 0],
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
);

const textOpacity = interpolate(
  sceneProgress,
  [10, 30, 45, 60],
  [0, 1, 1, 0],
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
);
```

**Required Assets:**
- `assets/scene2/creator-filming.jpg` - Creator with phone/ring light
- `assets/scene2/data-dashboard.jpg` - Analytics dashboard visualization
- `assets/scene2/viral-explosion.jpg` - Abstract viral/fire visual
- `assets/scene2/alert-phone.jpg` - Phone showing notification

---

### Scene 3: Title Reveal (0:11 - 0:15 | Frames 330-450)

**Visual Description:**
The montage dissolves into a blue graphical background. On the left, a rotating digital globe with orange/cyan trajectory lines arcing across it (representing global trend spread). The title "TRENDSCOPE" appears in large white sans-serif font on the right, followed by the tagline "The Bloomberg Terminal of Short-Form Video Trends" underneath.

**Technical Implementation:**

```typescript
// Scene 3: Title Reveal Component

// Background transition
const bgOpacity = interpolate(
  frame,
  [330, 345],
  [0, 1],
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
);

// Digital globe rotation
const globeRotation = interpolate(
  frame,
  [330, 450],
  [0, 120],
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
);

// Trajectory lines - animated arcs
const trajectoryLines = Array.from({ length: 5 }, (_, i) => ({
  startAngle: i * 72, // Evenly spaced
  length: interpolate(
    frame,
    [345 + i * 10, 390 + i * 10],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  ),
  color: i % 2 === 0 ? '#F59E0B' : '#00D9FF', // Orange/Cyan alternate
}));

// Title reveal - character by character or word by word
const titleProgress = interpolate(
  frame,
  [360, 400],
  [0, 1],
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
);

const titleOpacity = interpolate(
  frame,
  [360, 380],
  [0, 1],
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
);

const titleX = interpolate(
  frame,
  [360, 400],
  [100, 0],
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
);

// Tagline fade in
const taglineOpacity = interpolate(
  frame,
  [400, 420],
  [0, 1],
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
);

const taglineY = interpolate(
  frame,
  [400, 420],
  [20, 0],
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
);

// Final hold
const holdOpacity = interpolate(
  frame,
  [420, 450],
  [1, 1],
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
);
```

**Required Assets:**
- `assets/scene3/digital-globe.png` - Wireframe globe graphic

---

### Complete Composition Structure

```typescript
// Root.tsx addition
<Folder name="landing-intro">
  <Composition
    id="TrendscopeBloombergIntro"
    component={BloombergIntro}
    durationInFrames={450} // 15 seconds
    fps={30}
    width={1920}
    height={1080}
    defaultProps={{
      logoUrl: '/assets/scene1/trendscope-logo-white.png',
      montageImages: [
        '/assets/scene2/creator-filming.jpg',
        '/assets/scene2/data-dashboard.jpg',
        '/assets/scene2/viral-explosion.jpg',
        '/assets/scene2/alert-phone.jpg',
      ],
      globeUrl: '/assets/scene3/digital-globe.png',
    }}
  />
</Folder>
```

---

## Part 2: Image Generation Prompts

### Category A: Scene 1 Assets

#### A1: Trendscope Logo (White on Transparent)

**Prompt:**
```
Create a professional, modern wordmark logo for "TRENDSCOPE" on a transparent background. 
Style inspired by the Bloomberg logo - clean, authoritative, financial-terminal aesthetic.

SPECIFICATIONS:
- Text: "TRENDSCOPE" in all caps
- Font: Modern geometric sans-serif, similar to Bloomberg's font weight and spacing
- Color: Pure white (#FFFFFF)
- Style: Clean, bold, professional
- Background: Transparent (PNG alpha channel)

STYLE DETAILS:
- Letter spacing: Slightly tight, professional
- Weight: Bold/semi-bold
- Slight forward lean or momentum suggestion
- Subtle tech/finance feel without being gimmicky
- Bloomberg Terminal-inspired authority

DIMENSIONS: 800px wide, 150px tall
FORMAT: PNG with transparency
```

---

### Category B: Scene 2 Montage Assets

#### B1: Creator Filming Scene

**Prompt:**
```
Professional photography-style image of a content creator filming a TikTok/short-form video. 
Bloomberg Brief-inspired aesthetic - high-end, cinematic, creator economy focus.

SCENE DETAILS:
- Young professional creator in modern studio/home setup
- Ring light visible, creating professional glow
- Holding smartphone on gimbal or tripod
- Confident, focused expression
- Modern, clean background (soft bokeh)

AESTHETIC:
- Bloomberg Terminal color grading: Cool blues, slight teal/cyan tint
- Professional, high-production value
- Golden hour or studio lighting
- Slight depth of field
- Premium feel (not amateur/stock photo look)

COLOR PALETTE:
- Primary: Cool blues (#3B82F6, #0EA5E9)
- Accents: Cyan highlights (#00D9FF)
- Warm skin tones balanced with cool environment

MOOD: Professional, creative, focused, modern
DIMENSIONS: 1920x1080 (16:9 landscape)
STYLE: Cinematic photography, Bloomberg editorial aesthetic
```

#### B2: Data Dashboard with Velocity Charts

**Prompt:**
```
Abstract data visualization dashboard showing trend velocity metrics. 
Bloomberg Terminal meets TikTok analytics aesthetic.

VISUAL ELEMENTS:
- Multiple trend line graphs showing upward momentum
- Velocity indicators (speedometers or progress bars)
- Numerical data displays: "+340%", "2.4M views", "Velocity: 89/100"
- Waveform visualizations suggesting audio/sound trends
- Grid layout like a professional trading terminal

AESTHETIC:
- Dark background (#0F172A or #020617)
- Bright cyan (#00D9FF) and blue (#3B82F6) accent lines
- Green (#10B981) for positive growth indicators
- Glowing data points and lines
- Subtle grid overlay
- Modern, high-tech financial terminal look

TEXT ELEMENTS (subtle):
- "VELOCITY"
- "TREND SIGNAL"
- "SATURATION: 12%"
- Abstract timestamps and data points

MOOD: Data-driven, fast-paced, intelligent, professional
DIMENSIONS: 1920x1080
STYLE: UI/UX mockup, Bloomberg Terminal aesthetic, dark mode interface
```

#### B3: Viral Explosion / Trend Ignition

**Prompt:**
```
Abstract visualization of a viral trend exploding - representing the moment a trend catches fire.
Dynamic, energetic, motion-blur aesthetic.

VISUAL CONCEPT:
- Abstract light burst/explosion from center
- Sound wave ripples emanating outward
- Particle effects suggesting rapid spread
- Abstract representation of content going viral
- Could be: Abstract fire, light burst, or particle explosion

AESTHETIC:
- Bloomberg-inspired color grading
- Cyan (#00D9FF) and blue (#3B82F6) energy bursts
- Orange/amber (#F59E0B) heat/core elements
- Motion blur effects
- High contrast, dynamic composition
- Suggests speed and exponential growth

COMPOSITION:
- Central burst point
- Radiating energy lines
- Abstract video/content icons dissolving in the energy
- Sense of rapid expansion

MOOD: Explosive, exciting, fast, viral, breakthrough moment
DIMENSIONS: 1920x1080
STYLE: Abstract digital art, motion graphics still, energy visualization
```

#### B4: Alert Notification on Phone

**Prompt:**
```
Close-up of a smartphone displaying a trend alert notification. 
Professional product photography aesthetic with Bloomberg Terminal-inspired UI.

SCENE DETAILS:
- Modern smartphone (iPhone or similar) at slight angle
- Screen showing notification: "🔥 TREND ALERT"
- Notification details visible: "Sound 'Soft Glam' surging +340% in #beauty"
- Professional hand or clean surface holding phone
- Soft, professional lighting

AESTHETIC:
- Bloomberg color palette: Deep blues, cyan accents
- Clean, minimal background (desk, studio)
- Professional depth of field
- High-end product photography style
- Slight reflection on phone screen

NOTIFICATION UI:
- Dark mode interface (#0F172A background)
- Cyan (#00D9FF) accent for urgency
- Green (#10B981) for positive growth indicator
- Clean typography, Bloomberg Terminal-inspired
- "Trendscope" app branding subtle

MOOD: Urgent but professional, actionable, timely
DIMENSIONS: 1920x1080
STYLE: Product photography, tech editorial, Bloomberg Businessweek aesthetic
```

---

### Category C: Scene 3 Assets

#### C1: Digital Globe (Wireframe Style)

**Prompt:**
```
Digital wireframe globe for video animation - representing global trend spread.
Bloomberg Terminal meets tech visualization aesthetic.

VISUAL SPECIFICATIONS:
- Wireframe/spherical grid globe
- Latitude and longitude lines
- Slight transparency/ghostly quality
- Designed for rotation animation
- Centered composition

AESTHETIC:
- Dark blue background (#0F172A)
- Cyan (#00D9FF) wireframe lines with glow effect
- Subtle blue (#3B82F6) secondary lines
- Glowing data points on major cities/nodes
- Tech/finance terminal feel

DETAILS:
- Clean geometric lines
- Subtle glow/bloom on wireframe
- Optional: Small glowing dots at major cities (NYC, London, Tokyo, etc.)
- Rotation-ready (symmetrical design)
- Professional, data-driven aesthetic

MOOD: Global, connected, data-driven, professional
DIMENSIONS: 800x800px (square for rotation), transparent background
STYLE: 3D wireframe render, tech visualization, Bloomberg Terminal graphic
```

---

### Category D: Optional Supporting Assets

#### D1: Curved Sweep Lines (Overlay)

**Prompt:**
```
Abstract curved white lines for video overlay animation.
Thin, elegant arc lines sweeping across screen.

SPECIFICATIONS:
- Multiple curved arc paths
- White/cyan gradient lines
- Varying thickness (1-3px)
- Semi-transparent (60-80% opacity)
- Smooth, elegant curves

STYLE:
- Bloomberg Terminal-inspired data visualization
- Suggests data flow, connectivity, movement
- Clean, minimal, professional
- Subtle glow effect

FORMAT: PNG with transparency, or SVG paths
DIMENSIONS: 1920x1080
USE: Overlay graphics for video transitions
```

#### D2: Particle Effect Elements

**Prompt:**
```
Small glowing particle dots for video background animation.
Cyan/blue glowing orbs for floating particle effects.

SPECIFICATIONS:
- Multiple small circular dots (4-12px diameter)
- Cyan (#00D9FF) and blue (#3B82F6) colors
- Soft glow/bloom effect
- Semi-transparent
- Various sizes for depth

STYLE:
- Tech/finance terminal aesthetic
- Data dust, digital particles
- Suggests data points, activity, energy
- Clean, modern, subtle

FORMAT: PNG sprite sheet or individual PNGs
DIMENSIONS: Individual particles 16x16px to 32x32px
USE: Background animation elements
```

---

## Part 3: Technical Specifications for Remotion

### Color Palette (Exact Hex Values)

```typescript
const COLORS = {
  // Backgrounds
  bgDark: '#020617',        // Deepest background
  bgCard: '#0F172A',        // Card/dashboard background
  bgElevated: '#1E293B',    // Elevated surfaces
  
  // Accents
  accentCyan: '#00D9FF',    // Primary highlight
  accentBlue: '#3B82F6',    // Secondary highlight
  accentOrange: '#F59E0B',  // Trajectory/warning
  
  // Semantic
  success: '#10B981',       // Growth indicators
  white: '#FFFFFF',         // Text
  white70: 'rgba(255,255,255,0.7)', // Secondary text
  
  // Gradients
  gradientPrimary: 'linear-gradient(135deg, #3B82F6 0%, #00D9FF 100%)',
  gradientDark: 'linear-gradient(180deg, #0F172A 0%, #020617 100%)',
};
```

### Typography

```typescript
const TYPOGRAPHY = {
  // Main title (Scene 3)
  title: {
    fontFamily: 'Inter, system-ui, sans-serif',
    fontSize: 120,
    fontWeight: 800,
    letterSpacing: '-0.02em',
    color: '#FFFFFF',
  },
  
  // Tagline
  tagline: {
    fontFamily: 'Inter, system-ui, sans-serif',
    fontSize: 32,
    fontWeight: 400,
    letterSpacing: '0.02em',
    color: 'rgba(255,255,255,0.7)',
  },
  
  // Montage text overlays
  montageText: {
    fontFamily: 'Inter, system-ui, sans-serif',
    fontSize: 64,
    fontWeight: 700,
    letterSpacing: '-0.01em',
    color: '#FFFFFF',
    textTransform: 'uppercase',
  },
};
```

### Animation Easings

```typescript
// Use these easing functions for consistency
import { Easing } from 'remotion';

const EASINGS = {
  // Entrance animations
  entrance: Easing.out(Easing.cubic),
  
  // Exit animations  
  exit: Easing.in(Easing.cubic),
  
  // General smooth
  smooth: Easing.inOut(Easing.cubic),
  
  // Dramatic
  dramatic: Easing.out(Easing.exp),
  
  // For sliding tiles
  slide: Easing.out(Easing.quart),
};
```

---

## Part 4: File Structure

```
remotion/
├── src/
│   ├── compositions/
│   │   ├── BloombergIntro.tsx       # Main composition
│   │   ├── Scene1LogoReveal.tsx     # Scene 1 component
│   │   ├── Scene2Montage.tsx        # Scene 2 component
│   │   └── Scene3TitleReveal.tsx    # Scene 3 component
│   ├── components/
│   │   ├── OrbitalRings.tsx         # Animated rings
│   │   ├── SlidingTiles.tsx         # Tile transition effect
│   │   ├── DigitalGlobe.tsx         # Rotating globe
│   │   └── ParticleField.tsx        # Floating particles
│   └── Root.tsx                     # Register composition
├── assets/
│   ├── scene1/
│   │   └── trendscope-logo-white.png
│   ├── scene2/
│   │   ├── creator-filming.jpg
│   │   ├── data-dashboard.jpg
│   │   ├── viral-explosion.jpg
│   │   └── alert-phone.jpg
│   └── scene3/
│       └── digital-globe.png
└── public/
    └── videos/
        └── trendscope-intro.mp4     # Final output
```

---

## Part 5: Rendering Instructions

### Development
```bash
# Start Remotion Studio for preview
cmd /c "cd remotion && npm run dev"
# Open http://localhost:3003
```

### Production Render
```bash
# Render to frontend public folder
cmd /c "cd remotion && npx remotion render TrendscopeBloombergIntro ../frontend/public/videos/trendscope-intro.mp4 --codec=h264 --crf=18"
```

### Quality Settings
- **Codec:** H.264 (for web compatibility)
- **CRF:** 18 (high quality)
- **FPS:** 30
- **Resolution:** 1920x1080

---

## Part 6: Agent Checklist

Before claiming completion, verify:

- [ ] All 3 scenes implemented with correct timings
- [ ] Scene 1: Orbital rings rotating correctly
- [ ] Scene 1: Logo fades in at 1.5s mark
- [ ] Scene 2: 4 montage scenes with sliding tile effect
- [ ] Scene 2: Text overlays animate with each scene
- [ ] Scene 3: Digital globe rotates
- [ ] Scene 3: Title "TRENDSCOPE" reveals
- [ ] Scene 3: Tagline appears
- [ ] All colors match brand palette exactly
- [ ] Typography uses Inter font family
- [ ] Video renders successfully to MP4
- [ ] Final video plays smoothly at 30fps
- [ ] All image assets loaded from `/assets/` paths

---

---

## Part 7: Alternative Logo Option (Bloomberg-Style Wordmark)

> **Recommendation:** Use this Bloomberg-inspired wordmark for the intro video and hero branding. Keep the current icon+wordmark for app UI/navigation.

### Why a New Logo for the Video?

While the current Trendscope logo (trend line icon + wordmark) works well for app UI, it doesn't fully capture the **Bloomberg Terminal gravitas** needed for the intro video positioning.

| Current Logo | Bloomberg Style Needed |
|--------------|------------------------|
| Friendly app icon + wordmark | Authoritative wordmark only |
| Rounded, approachable corners | Sharp, terminal-grade precision |
| "SaaS tool" vibe | "Financial terminal" authority |
| Works well in navigation | Commands screen presence |

### A1-ALT: Bloomberg-Style Trendscope Wordmark (REVISED)

**Prompt for Image Generation:**
```
Create a professional, authoritative wordmark logo for "TRENDSCOPE" - styled as "The Bloomberg Terminal of Short-Form Video Trends." CRITICAL CONSTRAINTS BELOW.

⚠️  CRITICAL CONSTRAINTS - MUST FOLLOW EXACTLY:
1. UPRIGHT LETTERS ONLY - ZERO ITALIC, ZERO SLANT, NO ANGLE
2. TIGHT LETTER-SPACING - letters almost touching, architectural density
3. GEOMETRIC PRECISION - perfect circles for O, sharp angles for T and N
4. NO DYNAMIC/FLOWING FEEL - static, grounded, authoritative

DESIGN SPECIFICATIONS:
- Text: "TRENDSCOPE" in ALL CAPS
- Font: Geometric sans-serif, BOLD/HEAVY weight (800-900)
- Letter-spacing: VERY TIGHT (-0.04em), architectural, compact
- Orientation: PERFECTLY UPRIGHT (0° angle), vertical strokes are 90° vertical
- Color: Pure white (#FFFFFF)
- Background: Transparent (PNG alpha)
- NO icon, NO symbol - text-only wordmark

TYPOGRAPHY - EXACT REQUIREMENTS:
- "T" - Strong vertical stem, sharp right angles, no curves
- "R" - Geometric leg, precise corner where bowl meets stem
- "E" - Equal bar lengths, squared terminals
- "N" - Sharp vertex, straight diagonal, no rounded joints
- "D" - Perfect semicircle bowl meeting straight vertical stem
- "S" - Symmetric, geometric curves (no calligraphic flow)
- "C" - Perfect arc, geometric, no tapering
- "O" - Perfect circle/oval, geometric precision
- "P" - Bowl perfectly round, stem straight vertical
- "E" - Same as first E, consistent

MOOD - MUST CONVEY:
- Financial terminal authority (think Bloomberg terminal screen)
- News organization gravitas (Reuters, AP, Dow Jones)
- Data infrastructure precision (AWS, Snowflake, Palantir)
- ZERO marketing/creative agency feel
- ZERO Nike/advertising dynamic energy
- Static, grounded, institutional, serious

NEGATIVE CONSTRAINTS (DO NOT INCLUDE):
- NO italic or slanted text
- NO forward lean or angle
- NO loose spacing
- NO flowing, script-like, or calligraphic curves
- NO marketing/advertising agency aesthetic
- NO "dynamic" or "energetic" feel
- NO rounded, friendly terminals

VISUAL REFERENCES:
- Bloomberg terminal screen text
- Reuters logo wordmark spacing
- Financial Times masthead weight
- IBM Plex Bold geometric precision
- Terminal monospace authority but in geometric sans-serif

TECHNICAL:
- Transparent PNG, 2000px wide minimum
- Pixel-perfect edges, no blur
- High contrast white on transparent only
- Works at 200px (small) and 2000px (hero)
```

**Usage Strategy:**
| Context | Logo Variant |
|---------|--------------|
| Intro video (center screen) | Bloomberg-style wordmark (A1-ALT) |
| Landing page hero | Bloomberg-style wordmark (A1-ALT) |
| App UI / Navigation | Current icon+wordmark |
| Favicon / Small sizes | Current icon only |

---

*Plan Version: 1.0*  
*Created: 2026-02-20*  
*For: Trendscope Landing Page Intro Video*
