# Trendscope Remotion Video Generation

Complete guide for using, maintaining, and extending the Remotion video generation system in the Trendscope project.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & React Version Isolation](#architecture--react-version-isolation)
3. [Project Structure](#project-structure)
4. [Available Commands](#available-commands)
5. [Creating Video Compositions](#creating-video-compositions)
6. [Rendering Videos](#rendering-videos)
7. [Integration with Frontend](#integration-with-frontend)
8. [Design System & Branding](#design-system--branding)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Overview

This Remotion project generates marketing videos, trend reports, and social media content for Trendscope. It runs as a **separate Node.js project** to avoid React version conflicts with the main Next.js frontend.

### Key Features
- 🎬 Programmatic video generation
- 🎨 Consistent brand styling with Trendscope design system
- 📱 Multiple formats (16:9, 9:16 for Stories)
- ⚡ On-demand rendering via API/backend integration
- 🖼️ Output to frontend public folder for immediate use

---

## Architecture & React Version Isolation

### ⚠️ Critical: React Version Separation

| Project | React Version | Purpose |
|---------|--------------|---------|
| `frontend/` | React 19 | Next.js web application |
| `remotion/` | React 18 | Video generation |

**Why separate?** Remotion is optimized for React 18. The frontend uses React 19. Mixing versions causes runtime errors.

### Folder Isolation

```
trendscope/
├── frontend/          ← React 19, Next.js 15
│   ├── package.json   ← react: ^19.0.0
│   └── public/videos/ ← Output destination
│
└── remotion/          ← React 18, Remotion 4
    ├── package.json   ← react: ^18.3.1
    └── src/           ← Compositions
```

### Never Import Between Projects

❌ **DON'T:**
```typescript
// WRONG - Never import from frontend into remotion
import { Component } from '../frontend/components/Button';
```

✅ **DO:**
```typescript
// CORRECT - Keep compositions self-contained
import { MyComponent } from './components/MyComponent';
```

---

## Project Structure

```
remotion/
├── src/
│   ├── index.ts                 # Entry point - registers Root
│   ├── Root.tsx                 # Defines all compositions
│   ├── compositions/            # Video scene definitions
│   │   ├── TrendReport.tsx      # Trend report video
│   │   └── MarketingHero.tsx    # Marketing hero video
│   ├── components/              # Reusable video components
│   └── styles/
│       └── index.css            # Tailwind + custom styles
├── package.json                 # React 18 dependencies
├── tsconfig.json                # TypeScript config
├── tailwind.config.ts           # Brand-matched Tailwind
├── remotion.config.ts           # Remotion settings
├── postcss.config.js            # PostCSS for Tailwind
└── README_remotion.md           # This file
```

---

## Available Commands

All commands run from the `remotion/` directory:

```bash
# Start development studio (visual editor)
cmd /c "cd remotion && npm run dev"
# Opens at http://localhost:3003

# List available compositions
cmd /c "cd remotion && npx remotion compositions"

# Render a video
cmd /c "cd remotion && npx remotion render <composition-id> <output-path>"

# Example: Render to frontend public folder
cmd /c "cd remotion && npx remotion render TrendReport ../frontend/public/videos/trend-report.mp4"

# Upgrade Remotion
cmd /c "cd remotion && npm run upgrade"
```

### PowerShell Alternative

If you have execution policy issues:
```powershell
cmd /c "cd remotion && npm run dev"
```

---

## Creating Video Compositions

### 1. Create a New Composition File

Create `src/compositions/MyVideo.tsx`:

```typescript
import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  Easing,
} from 'remotion';

interface MyVideoProps {
  title: string;
  subtitle: string;
}

export const MyVideo: React.FC<MyVideoProps> = ({ title, subtitle }) => {
  const frame = useCurrentFrame();
  
  // Animate from frame 0 to 30
  const opacity = interpolate(
    frame,
    [0, 30],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(135deg, #0066FF 0%, #00D9FF 100%)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <h1 style={{ opacity, color: 'white', fontSize: 72 }}>
        {title}
      </h1>
      <p style={{ opacity, color: 'white', fontSize: 32 }}>
        {subtitle}
      </p>
    </AbsoluteFill>
  );
};
```

### 2. Register in Root.tsx

Add to `src/Root.tsx`:

```typescript
import { MyVideo } from './compositions/MyVideo';

// Inside the Root component:
<Composition
  id="MyVideo"                    # Unique identifier
  component={MyVideo}
  durationInFrames={30 * 10}      # 10 seconds at 30fps
  fps={30}
  width={1920}
  height={1080}
  defaultProps={{
    title: 'My Title',
    subtitle: 'My Subtitle',
  }}
/>
```

### 3. Folder Naming Rules

Folder names can only contain: `a-z`, `A-Z`, `0-9`, `-`

```typescript
// ✅ CORRECT
<Folder name="marketing-videos">
<Folder name="socialMedia">

// ❌ WRONG - Spaces not allowed
<Folder name="Marketing Videos">
<Folder name="Social Media">
```

---

## Rendering Videos

### Manual Rendering

```bash
# Basic render
cmd /c "cd remotion && npx remotion render TrendReport output.mp4"

# Render to frontend public folder (recommended)
cmd /c "cd remotion && npx remotion render TrendReport ../frontend/public/videos/trend-report.mp4"

# Render with props
cmd /c "cd remotion && npx remotion render TrendReport output.mp4 --props='{\"title\":\"Custom Title\"}'"

# Render specific frame range
cmd /c "cd remotion && npx remotion render TrendReport output.mp4 --frames=0-100"

# Render with different quality
cmd /c "cd remotion && npx remotion render TrendReport output.mp4 --codec=h264 --crf=18"
```

### Programmatic Rendering (from Backend)

Python example:
```python
import subprocess

result = subprocess.run([
    'npx', 'remotion', 'render', 
    'TrendReport', 
    '../frontend/public/videos/output.mp4',
    '--props={"title":"Weekly Report"}'
], cwd='remotion', capture_output=True, text=True)

if result.returncode == 0:
    print("Video rendered successfully!")
else:
    print(f"Error: {result.stderr}")
```

### Available Codecs

| Codec | Extension | Best For |
|-------|-----------|----------|
| h264 | .mp4 | Web playback, compatibility |
| h265 | .mp4 | Smaller file sizes |
| vp8 | .webm | Web streaming |
| vp9 | .webm | High quality web |
| prores | .mov | Professional editing |
| gif | .gif | Animations (limited) |

---

## Integration with Frontend

### Video Output Flow

```
1. User triggers action (e.g., clicks "Generate Report")
   ↓
2. Frontend calls API endpoint
   ↓
3. Backend/Next.js API runs Remotion render
   ↓
4. Video saved to frontend/public/videos/
   ↓
5. Frontend immediately displays video
```

### Next.js API Route Example

Create `frontend/app/api/generate-video/route.ts`:

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

export async function POST(req: NextRequest) {
  try {
    const { compositionId, props } = await req.json();
    
    const outputPath = path.join(
      process.cwd(), 
      'public', 
      'videos', 
      `${compositionId}-${Date.now()}.mp4`
    );
    
    const propsArg = props ? `--props='${JSON.stringify(props)}'` : '';
    
    await execAsync(
      `npx remotion render ${compositionId} ${outputPath} ${propsArg}`,
      { cwd: path.join(process.cwd(), '..', 'remotion') }
    );
    
    const publicPath = outputPath.replace(process.cwd(), '').replace('/public', '');
    
    return NextResponse.json({ 
      success: true, 
      videoUrl: publicPath 
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: String(error) },
      { status: 500 }
    );
  }
}
```

### Using Videos in Frontend

```tsx
// Standard HTML video
<video 
  src="/videos/trend-report.mp4" 
  controls 
  width="100%"
/>

// Next.js Image component (for thumbnails)
import Image from 'next/image';

<Image
  src="/videos/trend-report-thumb.jpg"
  alt="Trend Report"
  width={1920}
  height={1080}
/>
```

---

## Design System & Branding

### Brand Colors

Use these exact colors for brand consistency:

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-brand-primary` | `#0066FF` | CTAs, primary elements |
| `--color-brand-accent` | `#00D9FF` | Highlights, velocity |
| `--color-brand-success` | `#00C853` | Positive growth |
| `--color-brand-warning` | `#FFC107` | Warnings |
| `--color-brand-danger` | `#FF3B30` | Errors, alerts |
| `--color-brand-secondary` | `#1A1A1A` | Text, headings |

### Typography

```typescript
// Primary font (body text)
fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif'

// Display font (headings)
fontFamily: 'Clash Display, ui-sans-serif, system-ui, sans-serif'
```

### Animation Patterns

```typescript
// Entrance animation
const entrance = interpolate(
  frame,
  [0, 30],
  [100, 0],
  { easing: Easing.out(Easing.cubic) }
);

// Fade in
const fadeIn = interpolate(
  frame,
  [0, 20],
  [0, 1],
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
);

// Spring animation
import { spring } from 'remotion';

const scale = spring({
  frame,
  fps,
  config: { damping: 12, stiffness: 100 },
});
```

### Updating Brand Colors

If brand colors change, update in:
1. `remotion/tailwind.config.ts`
2. `remotion/src/styles/index.css`
3. All composition files

---

## Troubleshooting

### "Cannot find module 'react'"

**Cause:** Running from wrong directory or React not installed.

**Fix:**
```bash
cd remotion
npm install
```

### "Folder name can only contain a-z, A-Z, 0-9 and -"

**Cause:** Folder name has spaces or special characters.

**Fix:** Rename folders in `Root.tsx`:
```typescript
// ❌ Wrong
<Folder name="Marketing Videos">

// ✅ Correct
<Folder name="marketing-videos">
```

### Render fails with timeout

**Cause:** Complex animation or insufficient memory.

**Fix:**
```bash
# Increase timeout
cmd /c "cd remotion && npx remotion render TrendReport output.mp4 --timeout=60000"

# Reduce concurrency
cmd /c "cd remotion && npx remotion render TrendReport output.mp4 --concurrency=1"
```

### Video plays but shows blank/black frames

**Cause:** `delayRender()` not resolved or composition error.

**Fix:** Check browser console in Remotion Studio for errors.

### Port conflicts (3003)

**Cause:** Another service using port 3003.

**Fix:** Change port in `remotion.config.ts`:
```typescript
setPort: 3004,
```

### Fonts not loading

**Fix:** Use system fonts or embed fonts:
```typescript
// Use system fonts as fallback
fontFamily: 'Inter, Arial, sans-serif'

// Or load Google Fonts in composition
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
```

---

## Best Practices

### 1. Keep Compositions Small

Split large videos into sequences:

```typescript
<Sequence from={0} durationInFrames={90}>
  <Intro />
</Sequence>
<Sequence from={90} durationInFrames={180}>
  <Content />
</Sequence>
<Sequence from={270} durationInFrames={60}>
  <Outro />
</Sequence>
```

### 2. Use TypeScript for Props

```typescript
interface VideoProps {
  title: string;
  subtitle?: string;
  trends: Array<{ name: string; growth: string }>;
}
```

### 3. Preview in Studio Before Rendering

Always test in the Remotion Studio before batch rendering:
```bash
cmd /c "cd remotion && npm run dev"
```

### 4. Clean Up Generated Videos

Add to `.gitignore` in project root:
```gitignore
# Generated videos (keep folder, ignore files)
frontend/public/videos/*.mp4
frontend/public/videos/*.webm
!frontend/public/videos/.gitkeep
```

### 5. Version Lock Remotion

Don't auto-update Remotion in production. Test updates first:
```json
{
  "dependencies": {
    "remotion": "4.0.280"  // Exact version
  }
}
```

### 6. Git Ignore Node Modules

Ensure `remotion/node_modules/` is in `.gitignore`:
```gitignore
# Remotion
remotion/node_modules/
remotion/dist/
remotion/out/
```

---

## Maintenance Checklist

### Monthly
- [ ] Check for Remotion updates: `npm run upgrade`
- [ ] Review and clean old videos from `frontend/public/videos/`
- [ ] Verify React 18/19 separation is maintained

### When Frontend Changes
- [ ] Update brand colors in `tailwind.config.ts`
- [ ] Sync any font changes
- [ ] Test existing compositions still render correctly

### Before Production Deploy
- [ ] Test render on production-like environment
- [ ] Verify output path is correct
- [ ] Check video playback in target browsers

---

## Resources

- [Remotion Docs](https://www.remotion.dev/docs)
- [Remotion GitHub](https://github.com/remotion-dev/remotion)
- [Animation Examples](https://www.remotion.dev/showcase)
- [Tailwind CSS](https://tailwindcss.com/docs)

---

## Support

For issues specific to:
- **Remotion**: Check [Remotion Discord](https://remotion.dev/discord) or GitHub
- **Trendscope Integration**: Contact the development team

---

*Last updated: 2026-02-20*
*Remotion Version: 4.0.280*
*React Version: 18.3.1*
