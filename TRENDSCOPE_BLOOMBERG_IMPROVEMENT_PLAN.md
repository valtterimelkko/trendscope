# Trendscope Bloomberg-Style Video Improvement Plan

> **Goal:** Elevate the Trendscope intro video to match the broadcast-quality motion graphics of Bloomberg Brief

---

## Executive Summary

This document provides two implementation paths for improving the Trendscope intro video:

| Aspect | Option A: Incremental | Option B: Full Recreation |
|--------|----------------------|---------------------------|
| **Effort** | 1-2 days | 3-4 days |
| **Complexity** | Low-Medium | Medium-High |
| **Impact** | Significant | Maximum |
| **New Dependencies** | None | `@remotion/three`, `@remotion/transitions` |
| **Asset Count** | 3-5 new images | 8-10 new images + 3D globe |

**Reference Materials:**
- **Baseline Video (START HERE):** `frontend/public/videos/trendscope-intro-v8.mp4`
- Previous Version: `frontend/public/videos/trendscope-intro-v7.mp4`
- Bloomberg Reference: `bloomberg_brief_30s.webm`
- Original Plan: `TRENDSCOPE_BLOOMBERG_VIDEO_PLAN.md`
- Remotion Docs: `remotion/README_remotion.md`
- Remotion Skills: `/root/.claude/skills/remotion/`
- **Base Composition:** `BloombergIntroV8.tsx`

---

## LOGO SPECIFICATION (Applies to Both Options A & B)

### Logo Asset Change

**CRITICAL:** Both Option A and Option B MUST use the new high-quality logo:

| Attribute | Specification |
|-----------|--------------|
| **Source File** | `logo/trendscope-logo-transparent.png` |
| **Destination** | `remotion/public/assets/scene1/trendscope-logo-transparent.png` |
| **Display Size** | 1000px width (V8 standard - doubled from V6/V7) |
| **Format** | PNG with transparency |
| **Quality** | High-resolution (1536x1024 original) |

### Why the Change?

The previous logo (`trendscope-logo-white.png`) had background removal artifacts and inconsistent edges. The new logo has:
- Clean, crisp edges
- Proper transparency
- Professional white text on transparent background
- Consistent with Bloomberg Terminal aesthetic

### Implementation Note

When implementing either Option A or B:
1. Copy `logo/trendscope-logo-transparent.png` to `remotion/public/assets/scene1/`
2. In the composition props, use: `logoUrl: 'assets/scene1/trendscope-logo-transparent.png'`
3. Use 1000px display width (V8 standard - see `BloombergIntroV8.tsx`)
4. Keep the same drop-shadow effect: `filter: 'drop-shadow(0 0 40px rgba(255,255,255,0.3))'`

---

## PART 1: OPTION A - INCREMENTAL IMPROVEMENT

### Overview

Enhance **Version 8** with broadcast-quality effects while keeping the current scene organization and timing. Focus on **glow effects, sliding transitions, and improved text animations**.

### Baseline

**Start from:** `BloombergIntroV8.tsx`
- 37-second duration (1110 frames @ 30fps)
- 1000px logo width
- High-quality transparent logo
- Extended scene timings from V3/V7

### Scene Structure (Retained from V8)

```
┌─────────────────────────────────────────────────────────────────┐
│  SCENE 1: ENHANCED LOGO REVEAL (0:00 - 0:04)                    │
│  ├── Dark blue background (#020617)                             │
│  ├── Two rotating orbital rings with SOFT GLOW                  │
│  ├── Curved sweep lines with motion blur effect                 │
│  ├── Floating particle field with depth                         │
│  └── "TRENDSCOPE" title with gradient + glow reveal             │
├─────────────────────────────────────────────────────────────────┤
│  SCENE 2: SLIDING TILE MONTAGE (0:04 - 0:22)                    │
│  ├── SLIDING TILE transition between scenes                     │
│  ├── Scene A: Creator filming ("DETECT EARLY")                  │
│  ├── Scene B: Data dashboard ("TRACK VELOCITY")                 │
│  ├── Scene C: Viral explosion ("BEAT THE DECAY")                │
│  └── Scene D: Phone alert ("CREATE FIRST")                      │
├─────────────────────────────────────────────────────────────────┤
│  SCENE 3: TITLE REVEAL (0:22 - 0:30)                            │
│  ├── Rotating wireframe globe (2D image with CSS 3D)            │
│  ├── Cyan/orange trajectory arcs                                │
│  └── "TRENDSCOPE" + tagline with spring animation               │
└─────────────────────────────────────────────────────────────────┘
```

### Technical Implementation Details

#### Scene 1: Enhanced Logo Reveal

**OrbitalRings Component (Enhanced):**
```typescript
// File: remotion/src/components/OrbitalRingsEnhanced.tsx
// Rings with CSS drop-shadow for glow effect
// Gradient stroke using SVG linearGradient
// Thicker ring width (8-12px vs current 2px)

const ringStyle = {
  filter: 'drop-shadow(0 0 20px rgba(0, 217, 255, 0.6))',
  stroke: 'url(#ringGradient)', // cyan to blue gradient
  strokeWidth: 10,
};
```

**CurvedSweepLines Component:**
```typescript
// File: remotion/src/components/CurvedSweepLines.tsx
// SVG paths with quadratic bezier curves
// 3 lines sweeping at different speeds/delays
// CSS blur filter for motion trail effect

const sweepPaths = [
  "M -200,200 Q 960,100 2120,300",
  "M -200,400 Q 960,200 2120,500", 
  "M -200,600 Q 960,800 2120,700"
];
```

**ParticleField Component:**
```typescript
// File: remotion/src/components/ParticleField.tsx
// 50-80 particles with varying sizes (2-6px)
// Upward float animation with slight horizontal drift
// Fade in/out at edges
// CSS blur for depth-of-field effect
```

**Text Reveal Animation:**
```typescript
// Gradient text fill
// text-shadow: 0 0 40px rgba(0, 217, 255, 0.5)
// Spring animation for scale (0.8 → 1.0)
// Subtle letter-spacing animation
```

#### Scene 2: Sliding Tile Montage

**SlidingTiles Transition Component:**
```typescript
// File: remotion/src/components/SlidingTiles.tsx
// Split screen into 5 horizontal strips (each 216px tall)
// Each strip slides from alternating directions
// Strip 1,3,5: Slide from RIGHT to LEFT
// Strip 2,4: Slide from LEFT to RIGHT
// Duration: 30 frames overlap between scenes
// Easing: Easing.out(Easing.cubic)

interface StripConfig {
  index: number;
  direction: 'left' | 'right';
  delay: number;
  image: string;
}
```

**Scene Timing:**
- Each scene displays for 90 frames (3 seconds)
- 30-frame sliding transition between scenes
- Text overlays animate with spring entrance

#### Scene 3: Title Reveal with Wireframe Globe

**WireframeGlobe Component:**
```typescript
// File: remotion/src/components/WireframeGlobe.tsx
// Use 2D wireframe globe image
// CSS 3D rotation transform
// Add glowing data points at city locations
// Trajectory arcs as SVG paths with draw-on animation

const globeRotation = interpolate(frame, [0, 180], [0, 120]);
```

**Trajectory Arcs:**
- 5 curved lines emanating from globe
- Alternating colors: cyan (#00D9FF) and orange (#F59E0B)
- Draw-on animation using stroke-dasharray
- Glow effect using CSS filter

### Implementation Checklist - Option A

#### Components to Create/Modify

- [ ] `OrbitalRingsEnhanced.tsx` - Add glow, gradient, thickness
- [ ] `CurvedSweepLines.tsx` - New curved line component
- [ ] `ParticleField.tsx` - Enhanced particle system
- [ ] `SlidingTiles.tsx` - New transition component
- [ ] `WireframeGlobe.tsx` - Rotating globe with arcs
- [ ] `SceneTransition.tsx` - Wrapper for sliding effect
- [ ] Update `BloombergIntro.tsx` - Main composition

#### Animation Improvements

- [ ] Scene 1: Add spring animation to text entrance
- [ ] Scene 1: Implement glow effects on all elements
- [ ] Scene 2: Implement sliding tile transitions
- [ ] Scene 2: Add Ken Burns effect (subtle zoom/pan) to images
- [ ] Scene 3: Add 3D rotation to globe image
- [ ] Scene 3: Animate trajectory arc drawing
- [ ] All scenes: Improve text reveal with gradient fills

---

## PART 2: OPTION B - FULL RECREATION

### Overview

A complete rebuild **starting from V8** using advanced Remotion features including **Three.js 3D globe**, **TransitionSeries**, **light leak overlays**, and **broadcast-style motion graphics**.

### Baseline

**Start from:** `BloombergIntroV8.tsx` (copy to `BloombergIntroV9.tsx` or new version)
- Use V8's scene timing (37 seconds) as foundation
- 1000px logo width
- High-quality transparent logo
- Build upon and enhance each scene

### Scene Structure (Enhanced)

```
┌─────────────────────────────────────────────────────────────────┐
│  SCENE 1: CINEMATIC OPEN (0:00 - 0:04)                          │
│  ├── Deep gradient background (animated subtle shift)           │
│  ├── 3D orbital rings with volumetric glow                      │
│  ├── Sweeping curved data lines with trail effect               │
│  ├── Particle field with depth layers                           │
│  └── "TRENDSCOPE" title with bloom/glow reveal                  │
├─────────────────────────────────────────────────────────────────┤
│  TRANSITION: Light leak overlay (0:04 - 0:05)                   │
├─────────────────────────────────────────────────────────────────┤
│  SCENE 2: SLIDING TILE MONTAGE (0:05 - 0:18)                    │
│  ├── Horizontal strip transitions with video-like motion        │
│  ├── Scene A: Creator filming + "DETECT EARLY"                  │
│  ├── Scene B: Data dashboard + "TRACK VELOCITY"                 │
│  ├── Scene C: Viral explosion + "BEAT THE DECAY"                │
│  └── Scene D: Phone alert + "CREATE FIRST"                      │
├─────────────────────────────────────────────────────────────────┤
│  TRANSITION: Globe emergence (0:18 - 0:20)                      │
├─────────────────────────────────────────────────────────────────┤
│  SCENE 3: GLOBAL TERMINAL (0:20 - 0:30)                         │
│  ├── Three.js 3D wireframe globe with rotation                  │
│  ├── Animated trajectory arcs connecting cities                 │
│  ├── Floating data points with pulse animation                  │
│  └── "TRENDSCOPE" + tagline with cinematic reveal               │
└─────────────────────────────────────────────────────────────────┘
```

### Technical Implementation Details

#### Prerequisites

```bash
# Install additional Remotion packages
cd remotion
npx remotion add @remotion/three
npx remotion add @remotion/transitions
npx remotion add @remotion/light-leaks
```

#### Scene 1: Cinematic Open

**GradientBackground Component:**
```typescript
// Animated gradient shift using interpolate
// Colors shift subtly between #020617 and #0a1628
// Creates "living" background
```

**VolumetricGlow Rings:**
```typescript
// Multiple ring layers for depth
// Inner ring: solid, bright
// Middle ring: soft glow
// Outer ring: faint halo
// All rotate at slightly different speeds
```

#### Scene 2: Sliding Tile Montage with TransitionSeries

```typescript
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { LightLeak } from "@remotion/light-leaks";

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}>
    <SceneDetectEarly />
  </TransitionSeries.Sequence>
  
  <TransitionSeries.Overlay durationInFrames={20}>
    <LightLeak />
  </TransitionSeries.Overlay>
  
  <TransitionSeries.Sequence durationInFrames={90}>
    <SceneTrackVelocity />
  </TransitionSeries.Sequence>
  
  <TransitionSeries.Transition
    presentation={slide({ direction: "from-left" })}
    timing={linearTiming({ durationInFrames: 15 })}
  />
  
  <TransitionSeries.Sequence durationInFrames={90}>
    <SceneBeatDecay />
  </TransitionSeries.Sequence>
</TransitionSeries>
```

**Custom SlidingTile Component:**
```typescript
// More sophisticated than Option A
// 7 strips for finer visual effect
// Strips have subtle rotation (1-2 degrees)
// Motion blur simulation during slide
// Edge vignette for focus
```

#### Scene 3: Three.js 3D Globe

```typescript
import { ThreeCanvas } from "@remotion/three";
import { useCurrentFrame } from "remotion";

const frame = useCurrentFrame();
const rotationY = frame * 0.02;

<ThreeCanvas width={1920} height={1080}>
  <ambientLight intensity={0.4} />
  <directionalLight position={[5, 5, 5]} intensity={0.8} />
  
  {/* Wireframe Globe */}
  <mesh rotation={[0, rotationY, 0]}>
    <sphereGeometry args={[3, 32, 32]} />
    <meshBasicMaterial 
      wireframe 
      color="#00D9FF"
      transparent
      opacity={0.6}
    />
  </mesh>
  
  {/* Inner solid core */}
  <mesh rotation={[0, rotationY, 0]}>
    <sphereGeometry args={[2.9, 32, 32]} />
    <meshBasicMaterial 
      color="#0F172A"
      transparent
      opacity={0.9}
    />
  </mesh>
  
  {/* Trajectory Arcs */}
  {/* Bezier curves connecting points on globe surface */}
</ThreeCanvas>
```

**TrajectoryArcs Component:**
```typescript
// 5 arcs connecting globe to edge of screen
// Arcs drawn using TubeGeometry along bezier curve
// Animated draw-on effect (scale from 0 to 1)
// Glow shader material
```

### Implementation Checklist - Option B

#### New Packages Required

- [ ] Install `@remotion/three`
- [ ] Install `@remotion/transitions`
- [ ] Install `@remotion/light-leaks`

#### Components to Create

- [ ] `CinematicBackground.tsx` - Animated gradient
- [ ] `VolumetricRings.tsx` - Multi-layer 3D rings
- [ ] `TrailSweepLines.tsx` - Lines with motion trails
- [ ] `AdvancedSlidingTiles.tsx` - 7-strip with rotation
- [ ] `ThreeGlobe.tsx` - Three.js wireframe globe
- [ ] `TrajectoryArcs3D.tsx` - 3D bezier curves
- [ ] `BloomRevealText.tsx` - Text with bloom effect
- [ ] Update `BloombergIntro.tsx` - New structure

#### Advanced Animations

- [ ] Implement TransitionSeries throughout
- [ ] Add LightLeak overlays between scenes
- [ ] Create 3D globe with Three.js
- [ ] Animate trajectory arcs in 3D space
- [ ] Add bloom/glow post-processing effects
- [ ] Implement Ken Burns on all images
- [ ] Add subtle camera movements

---

## PART 3: IMAGE ASSET PROMPTS

### Legend
- **A** = Needed for Option A (Incremental)
- **B** = Needed for Option B (Full Recreation)
- **Both** = Needed for both options

---

### ASSET 1: Wireframe Globe (Digital Style)

**For:** Both (A uses as 2D image, B uses as reference for 3D)

**Filename:** `assets/scene3/wireframe-globe-enhanced.png`

**Prompt:**
```
Create a high-resolution digital wireframe globe for video animation.

TECHNICAL SPECIFICATIONS:
- Transparent background (alpha channel)
- Resolution: 2000x2000px square
- Style: Clean geometric wireframe, technical visualization

GLOBE DETAILS:
- Perfect sphere with latitude and longitude lines
- Line weight: 2-3px for primary lines, 1px for secondary
- Grid pattern: 15-degree intervals
- Subtle glow/bloom on wireframe lines

COLOR PALETTE:
- Primary lines: Cyan #00D9FF with soft glow
- Secondary lines: Blue #3B82F6 (darker, no glow)
- Background: Transparent
- Data points: Small glowing dots at major cities

AESTHETIC:
- Bloomberg Terminal meets futuristic tech UI
- Clean, precise, professional
- Slight transparency/ghostly quality
- Data infrastructure visualization style

MOOD: Global, connected, data-driven, authoritative
STYLE: 3D wireframe render, tech visualization, Bloomberg Terminal graphic

NO: Surface textures, clouds, terrain, photographic elements
```

---

### ASSET 2: Creator Filming Scene (Enhanced)

**For:** Both

**Filename:** `assets/scene2/creator-filming-enhanced.jpg`

**Prompt:**
```
Professional cinematic photograph of a content creator filming TikTok/short-form video.
Bloomberg Brief-inspired aesthetic - high-end, cinematic, creator economy focus.

SCENE DETAILS:
- Young professional creator (diverse, 25-35 years old) in modern studio
- Ring light visible and illuminated, creating professional cyan/teal glow
- Holding smartphone on gimbal or tripod, actively filming
- Confident, focused expression, looking at phone
- Modern, clean background with soft bokeh effect
- Slight haze/atmospheric depth

AESTHETIC:
- Bloomberg Terminal color grading: Cool blues, cyan/teal tint
- Professional cinematic lighting with rim light
- Shallow depth of field (f/1.8 style blur)
- High production value, premium feel
- Shot on high-end cinema camera aesthetic

COLOR PALETTE:
- Dominant: Deep blues (#0F172A, #1E293B)
- Accent highlights: Cyan (#00D9FF), Teal (#14B8A6)
- Warm skin tones balanced with cool environment
- Subtle orange rim light for contrast

MOOD: Professional, creative, focused, modern, slightly mysterious
DIMENSIONS: 1920x1080 (16:9 landscape)
STYLE: Cinematic photography, Bloomberg editorial aesthetic, shallow DOF

TECHNICAL: Sharp focus on subject's face and phone, background softly blurred
```

---

### ASSET 3: Data Dashboard Visualization

**For:** Both

**Filename:** `assets/scene2/data-dashboard-enhanced.jpg`

**Prompt:**
```
Abstract data visualization dashboard showing trend velocity metrics.
Bloomberg Terminal meets modern SaaS dashboard aesthetic.

VISUAL ELEMENTS:
- Multiple trend line charts showing exponential growth patterns
- Candlestick-style charts with cyan/teal positive indicators
- Velocity indicators: speedometers showing "89/100"
- Numerical displays: "+340%", "2.4M views", trending upward
- Volume bar charts at bottom
- Grid layout like professional trading terminal (2x2 or 3x2 grid)
- Time series data, 30-day view

AESTHETIC:
- Dark background: #020617 to #0F172A gradient
- Bright cyan (#00D9FF) and teal (#14B8A6) accent lines
- Green (#00C853) for positive growth indicators
- Glowing data points and line endings
- Subtle grid overlay, very faint
- Glassmorphism effect on panels
- Modern, high-tech financial terminal look

TEXT ELEMENTS (subtle):
- "VELOCITY INDEX" header
- "TREND SIGNAL: STRONG"
- "SATURATION: 12%"
- Abstract timestamps

MOOD: Data-driven, fast-paced, intelligent, professional, exclusive
DIMENSIONS: 1920x1080
STYLE: UI/UX mockup, Bloomberg Terminal aesthetic, dark mode interface, glassmorphism

NO: Light mode elements, cluttered layout, amateur chart design
```

---

### ASSET 4: Viral Explosion / Trend Ignition

**For:** Both

**Filename:** `assets/scene2/viral-explosion-enhanced.jpg`

**Prompt:**
```
Abstract visualization of a viral trend exploding - representing the moment a trend catches fire.
Dynamic, energetic, motion-blur aesthetic with depth.

VISUAL CONCEPT:
- Central burst point with radiating energy
- Particle explosion emanating from center
- Sound wave ripples spreading outward
- Abstract light trails suggesting rapid movement
- Digital/tech aesthetic with organic energy

AESTHETIC:
- Deep space background: #020617 fading to black
- Cyan (#00D9FF) energy bursts as primary color
- Orange/amber (#F59E0B) heat at center/core
- Blue (#3B82F6) secondary energy lines
- Motion blur and streak effects
- High contrast, dynamic composition
- Suggests exponential growth and speed

COMPOSITION:
- Central bright burst point (slightly off-center)
- Radiating energy lines in all directions
- Foreground particles larger, background smaller
- Sense of depth and rapid expansion
- Leading lines drawing eye to center

MOOD: Explosive, exciting, fast, viral, breakthrough moment, energetic
DIMENSIONS: 1920x1080
STYLE: Abstract digital art, motion graphics still, energy visualization, particle system aesthetic

NO: Real objects, people, literal fire, text, UI elements
```

---

### ASSET 5: Phone Alert Notification

**For:** Both

**Filename:** `assets/scene2/phone-alert-enhanced.jpg`

**Prompt:**
```
Close-up of hands holding a smartphone displaying a trend alert notification.
Professional product photography with Bloomberg Terminal-inspired UI.

SCENE DETAILS:
- Modern smartphone (iPhone 15 Pro or similar) at 3/4 angle
- Screen showing "TREND ALERT" notification card
- Notification details: Trending sound, velocity percentage, category
- Professional hands holding phone naturally
- Soft, cinematic lighting with subtle cyan accent
- Clean, minimal dark background

NOTIFICATION UI DESIGN:
- Dark mode interface (#0F172A card on #020617 background)
- Cyan (#00D9FF) accent for urgency indicators
- Teal (#14B8A6) for trend name
- Green (#00C853) for positive growth metrics
- Clean typography, Bloomberg Terminal-inspired
- "Trendscope" branding subtle in header
- Card has subtle glassmorphism effect

AESTHETIC:
- High-end product photography
- Shallow depth of field (phone sharp, background blur)
- Slight reflection on phone screen
- Professional studio lighting
- Premium, exclusive feel

MOOD: Urgent but professional, actionable, timely, sophisticated
DIMENSIONS: 1920x1080
STYLE: Product photography, tech editorial, Bloomberg Businessweek aesthetic, cinematic

TECHNICAL: Sharp focus on phone screen, natural hand positioning, cinematic color grade
```

---

### ASSET 6: Abstract City/Skyline (For Ken Burns Effect)

**For:** Option B Only

**Filename:** `assets/scene2/city-skyline-abstract.jpg`

**Prompt:**
```
Abstract aerial view of modern city skyline at dusk.
Inspired by Bloomberg's city footage but stylized for brand consistency.

SCENE DETAILS:
- Modern financial district with iconic skyscrapers
- Aerial perspective looking down at angle
- Dusk/blue hour lighting (not night, not day)
- City lights beginning to illuminate
- Slight atmospheric haze/fog for depth
- One World Trade Center or similar iconic building visible

AESTHETIC:
- Cool color palette: blues (#1E293B, #334155), cyan tints
- Warm accent lights: amber/orange (#F59E0B) window lights
- Cinematic color grading
- Slight desaturation for sophisticated look
- High contrast between buildings and sky
- Subtle vignette effect

COMPOSITION:
- Rule of thirds placement of key buildings
- Leading lines from streets drawing eye inward
- Layered depth: foreground buildings, midground, background haze
- Dynamic angle suggesting movement

MOOD: Global, connected, professional, authoritative, urban energy
DIMENSIONS: 1920x1080 (16:9), high resolution for zoom
STYLE: Cinematic aerial photography, Bloomberg Brief aesthetic, blue hour

USAGE: Will be animated with slow zoom/pan (Ken Burns effect)
```

---

### ASSET 7: Trading Floor / Terminal Room

**For:** Option B Only

**Filename:** `assets/scene2/trading-floor-terminal.jpg`

**Prompt:**
```
Professional photograph of modern trading floor or data center.
Rows of screens showing financial data, Bloomberg Terminal aesthetic.

SCENE DETAILS:
- Multiple traders/analysts at workstations (3-4 people visible)
- Wall of monitors showing charts and data
- Modern office environment, clean and organized
- Screens glow with cyan/teal data visualizations
- Slight motion blur on people suggesting activity
- Professional attire, focused work

AESTHETIC:
- Cool ambient lighting with screen glow
- Dark environment illuminated by monitors
- Cyan (#00D9FF) and green (#00C853) screen accents
- Blue ambient (#0F172A, #1E293B)
- High-tech, professional atmosphere
- Slight grain for cinematic texture

COMPOSITION:
- Depth layers: foreground screens, midground workers, background wall of monitors
- Leading lines from desk rows
- Rule of thirds for human subjects
- Dynamic but not cluttered

MOOD: Serious, professional, data-driven, high-stakes, focused energy
DIMENSIONS: 1920x1080
STYLE: Documentary photography, Bloomberg terminal room aesthetic, cinematic
```

---

### ASSET 8: Global Network / Connectivity Visualization

**For:** Option B Only

**Filename:** `assets/scene3/global-network-nodes.jpg`

**Prompt:**
```
Abstract visualization of global data network and connectivity.
Represents worldwide trend spread and data flow.

VISUAL CONCEPT:
- World map or abstract representation of global connectivity
- Network nodes at major cities (glowing dots)
- Connection lines between nodes (arcs, not straight)
- Data flow visualization
- Abstract, not literal map

AESTHETIC:
- Dark background: #020617 fading to #0F172A
- Cyan (#00D9FF) primary nodes and connections
- Blue (#3B82F6) secondary nodes
- Orange (#F59E0B) accent highlights
- Glowing effects on all nodes
- Subtle grid or tech pattern overlay
- Digital, futuristic, clean

COMPOSITION:
- Centered or slightly offset globe/map
- Nodes distributed across major continents
- Connection lines create visual flow
- Depth layers: foreground glow, midground connections, background nodes

MOOD: Global reach, connected world, data flow, international, expansive
DIMENSIONS: 1920x1080
STYLE: Data visualization, network graph, futuristic tech aesthetic, Bloomberg Terminal style

NO: Literal map details, country borders, text labels, photographic elements
```

---

### ASSET 9: Light Leak / Lens Flare Elements (Overlay)

**For:** Option B Only

**Filename:** `assets/overlays/light-leak-overlay.png`

**Prompt:**
```
Abstract light leak and lens flare overlay for video transitions.
Designed to be composited over footage with "screen" or "add" blend mode.

ELEMENTS:
- Warm lens flare (orange/amber #F59E0B to yellow #FCD34D)
- Soft light leak from edge/corner
- Anamorphic streak effect
- Organic film light leak shapes

TECHNICAL:
- Transparent background (PNG with alpha)
- High resolution: 1920x1080
- Soft edges for seamless blending
- Multiple intensity zones

AESTHETIC:
- Analog film light leak aesthetic
- Warm tones: amber, gold, orange
- Soft, diffused glow
- Cinematic quality
- Professional broadcast transition feel

MOOD: Cinematic transition, warmth, premium quality, analog film nostalgia
DIMENSIONS: 1920x1080
STYLE: Film light leak, lens flare, anamorphic streak, overlay graphic

USAGE: Will be animated across screen during scene transitions
```

---

### ASSET 10: Trendscope Wordmark Logo (Enhanced)

**For:** Both

**Filename:** `assets/logo/trendscope-wordmark-enhanced.png`

**Prompt:**
```
Professional wordmark logo for "TRENDSCOPE" - enhanced version for video.
Bloomberg Terminal-inspired authority and precision.

SPECIFICATIONS:
- Text: "TRENDSCOPE" in ALL CAPS
- Transparent background (PNG alpha)
- High resolution: 2000px wide minimum
- Clean, pixel-perfect edges

TYPOGRAPHY:
- Font: Geometric sans-serif, BOLD weight (700-900)
- Letter-spacing: TIGHT (-0.02em), architectural density
- Perfectly upright (0° angle), no italic
- Geometric precision in letterforms

STYLE DETAILS:
- Color: Pure white (#FFFFFF) with subtle cyan glow effect
- Slight forward momentum suggested in letterforms
- Sharp, terminal-grade precision
- Authoritative, institutional feel
- Data infrastructure company aesthetic

MOOD: Financial terminal authority, news organization gravitas, data precision
STYLE: Bloomberg Terminal text, Reuters wordmark, IBM Plex Bold precision

NO: Rounded friendly terminals, script elements, icons, symbols
NOTE: This is text-only wordmark, no graphic icon
NOTE: Video uses 1000px width (V8 standard)
```

---

## PART 4: IMPLEMENTATION NOTES

### Color Palette Reference

```typescript
// Use these exact colors throughout both implementations
const COLORS = {
  // Backgrounds
  bgDark: '#020617',        // Deepest background
  bgCard: '#0F172A',        // Card/dashboard background
  bgElevated: '#1E293B',    // Elevated surfaces
  
  // Accents
  accentCyan: '#00D9FF',    // Primary highlight
  accentBlue: '#3B82F6',    // Secondary highlight
  accentTeal: '#14B8A6',    // Tertiary accent
  accentOrange: '#F59E0B',  // Trajectory/warning
  accentGreen: '#00C853',   // Success/positive
  
  // Text
  textWhite: '#FFFFFF',
  textMuted: 'rgba(255,255,255,0.7)',
  
  // Glows
  glowCyan: 'rgba(0, 217, 255, 0.5)',
  glowBlue: 'rgba(59, 130, 246, 0.4)',
};
```

### Typography Reference

```typescript
// Primary font for all text
const TYPOGRAPHY = {
  title: {
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
    fontWeight: 800,
    letterSpacing: '-0.02em',
  },
  subtitle: {
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
    fontWeight: 400,
    letterSpacing: '0.02em',
  },
  label: {
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
    fontWeight: 600,
    letterSpacing: '0.05em',
    textTransform: 'uppercase',
  }
};
```

### Animation Timing Standards

```typescript
// Consistent timing for both options
const TIMING = {
  sceneDuration: 90,        // 3 seconds at 30fps
  transitionDuration: 30,   // 1 second for transitions
  textEntranceDelay: 15,    // 0.5 second delay for text
  textEntranceDuration: 20, // 0.66 second for text animation
};

// Easing functions
const EASING = {
  entrance: Easing.out(Easing.cubic),
  exit: Easing.in(Easing.cubic),
  smooth: Easing.inOut(Easing.cubic),
  dramatic: Easing.out(Easing.exp),
};
```

### File Organization

```
remotion/
├── src/
│   ├── compositions/
│   │   ├── BloombergIntroV7.tsx          # Option A composition
│   │   └── BloombergIntroV8.tsx          # Option B composition
│   ├── components/
│   │   ├── option-a/                      # Option A components
│   │   │   ├── OrbitalRingsEnhanced.tsx
│   │   │   ├── CurvedSweepLines.tsx
│   │   │   ├── ParticleField.tsx
│   │   │   ├── SlidingTiles.tsx
│   │   │   └── WireframeGlobe2D.tsx
│   │   ├── option-b/                      # Option B components
│   │   │   ├── CinematicBackground.tsx
│   │   │   ├── VolumetricRings.tsx
│   │   │   ├── TrailSweepLines.tsx
│   │   │   ├── AdvancedSlidingTiles.tsx
│   │   │   ├── ThreeGlobe.tsx
│   │   │   ├── TrajectoryArcs3D.tsx
│   │   │   └── BloomRevealText.tsx
│   │   └── shared/                        # Shared components
│   │       ├── TextReveal.tsx
│   │       └── KenBurnsImage.tsx
│   └── Root.tsx
├── assets/
│   ├── scene1/                            # Scene 1 assets
│   ├── scene2/                            # Scene 2 assets
│   ├── scene3/                            # Scene 3 assets
│   ├── logo/                              # Logo assets
│   └── overlays/                          # Overlay assets
```

---

## PART 5: DECISION MATRIX

| Factor | Choose Option A If | Choose Option B If |
|--------|-------------------|-------------------|
| Timeline | Need quick turnaround (1-2 days) | Have 3-4 days available |
| Budget | Limited rendering budget | Can afford longer render times |
| Technical Risk | Prefer lower complexity | Comfortable with Three.js |
| Final Quality | "Significant improvement" acceptable | Want "broadcast quality" |
| Future Use | One-time use | Will reuse/iterate on video |
| Team Skills | No Three.js experience | Have React Three Fiber knowledge |

---

## Appendix: Reference Files

### Project Files
- Current implementation: `remotion/src/compositions/BloombergIntro.tsx`
- Existing assets: `remotion/public/assets/`
- Brand colors: Defined in `remotion/src/styles/index.css`

### Skills Documentation
- Remotion best practices: `/root/.claude/skills/remotion/SKILL.md`
- Asset generation: `/root/.claude/skills/remotion-assets/SKILL.md`
- 3D with Remotion: `/root/.claude/skills/remotion/rules/3d.md`
- Transitions: `/root/.claude/skills/remotion/rules/transitions.md`
- Timing/Easing: `/root/.claude/skills/remotion/rules/timing.md`
- Text animations: `/root/.claude/skills/remotion/rules/text-animations.md`

### External References
- Remotion docs: https://www.remotion.dev/docs
- React Three Fiber: https://docs.pmnd.rs/react-three-fiber
- Three.js docs: https://threejs.org/docs

---

*Plan Version: 1.0*
*Created: 2026-02-21*
*For: Trendscope Video Enhancement Project*
