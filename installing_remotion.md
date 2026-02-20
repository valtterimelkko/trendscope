# Remotion Installation Recommendation for Trendscope

**Date:** 2026-02-20  
**Context:** Installing Remotion for creating marketing animations in the Trendscope project

---

## Overview

This document outlines the recommended approach for integrating [Remotion](https://www.remotion.dev/) into the Trendscope project for creating on-demand marketing videos.

---

## Current Tech Stack Analysis

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 15 with React 19 |
| Styling | Tailwind CSS 4 |
| Charts | Recharts |
| Backend | Python |
| Package Manager | npm |

---

## Recommended Structure

```
/root/trendscope/
├── remotion/                    # Remotion project (separate from frontend)
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts       # Can share config with frontend
│   ├── src/
│   │   ├── index.tsx            # Entry point
│   │   ├── Root.tsx             # Compositions
│   │   ├── compositions/        # Video definitions
│   │   │   ├── TrendReport.tsx
│   │   │   └── MarketingHero.tsx
│   │   ├── components/          # Reusable video components
│   │   └── styles/              # Video-specific styles
│   └── out/                     # Default output folder (gitignored)
│
├── frontend/
│   ├── public/
│   │   └── videos/              # FINAL VIDEO DESTINATION
│   │       ├── trend-report-2024-02-20.mp4
│   │       └── marketing-hero.mp4
│   └── ...
```

---

## Key Decisions

### 1. Location: `/root/trendscope/remotion/`

**Rationale:**
- Videos are part of the project, version controlled together
- Clean separation from existing Python code
- Easy for Python backend to trigger video generation

### 2. React Version: 18 (Separate from Frontend's React 19)

**⚠️ Important Compatibility Note:**

Remotion works best with React 18. Since the frontend uses React 19, **Remotion should be a completely separate project** with its own `package.json` using React 18. This avoids version conflicts.

### 3. Video Output: `frontend/public/videos/`

**Why:**
- Videos become static assets served by Next.js
- Easy to reference in the app: `/videos/marketing-hero.mp4`
- Can use Next.js `<Video>` component or standard `<video>` tag
- Works with CDN if deployed to Vercel

---

## On-Demand Generation Flow

```
1. User clicks "Generate Video" in frontend
   ↓
2. Next.js API route calls Python backend
   ↓
3. Python runs: cd remotion && npx remotion render ...
   ↓
4. Video saved to frontend/public/videos/
   ↓
5. User can immediately view/download
```

**Alternative:** A Next.js API route can shell out to Remotion directly if preferred.

---

## Sharing Design System

**What CAN be shared:**
- Tailwind config (copy `frontend/tailwind.config.ts` → `remotion/tailwind.config.ts`)
- Color tokens
- Font settings
- Design tokens via shared JSON file

**What CANNOT be shared directly:**
- React components (due to React 18 vs 19 mismatch)

---

## Summary of Recommendations

| Decision | Choice |
|----------|--------|
| Location | `/root/trendscope/remotion/` |
| React Version | 18 (separate from frontend's React 19) |
| Video Output | `frontend/public/videos/` |
| Tailwind | Copy config from frontend |
| Trigger | Next.js API → shell command or Python subprocess |

---

## Future Considerations

### Remotion Lambda (Cloud Rendering)

For generating videos without blocking the server:
- Deploy Remotion to AWS Lambda
- Trigger via API
- Videos upload to S3 → CloudFront

Recommended for high-volume or long-running renders.

---

## Next Steps

To proceed with installation:

1. Scaffold the Remotion project at `/root/trendscope/remotion/`
2. Configure Tailwind to match the frontend
3. Set up the output directory to `frontend/public/videos/`
4. Create a sample marketing animation composition
5. Set up the API endpoint for on-demand generation

---

## Resources

- [Remotion Documentation](https://www.remotion.dev/docs)
- [Remotion GitHub](https://github.com/remotion-dev/remotion)
- [Remotion Brownfield Installation](https://www.remotion.dev/docs/brownfield)
