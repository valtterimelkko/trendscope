# Viral Waves - Product Intent Document

## Executive Summary

**Viral Waves** is a B2B SaaS platform that detects TikTok trends in their infancy—hours or days before they peak—enabling creators, agencies, and content teams to capitalize on viral moments while the window of opportunity is still open.

---

## The Core Problem We're Solving

### "Scrolling is not research."

For millions of TikTok creators, the only "trend research" available is endless, manual scrolling. This creates several critical pain points:

| Pain Point | Impact |
|------------|--------|
| **Trends die before discovery** | Sounds blow up and die in the same news cycle; formats spread across thousands of videos before lunch and burn out by dinner |
| **Agencies miss opportunities** | Internal processes can't keep pace with a platform that treats yesterday's trend like last year's news |
| **Creator burnout** | Hours of manual scrolling to find "what's working" steals time from actual content creation |
| **Reactive vs proactive** | By the time most creators notice a trend, it's already saturated |
| **No signal in the noise** | Viral content looks random; identifying *which* micro-trends will explode requires pattern recognition at scale |

### Why Speed Wins on TikTok

TikTok's algorithm creates **compressed trend lifecycles**:
- A sound can go from zero to millions of uses in 24-48 hours
- The "early adopter window" for creators to benefit from a trend is often 6-24 hours
- Once a trend hits mainstream, engagement rates drop precipitously
- **Speed of detection directly correlates with creator success**

---

## The Solution: Viral Waves

### Core Value Proposition

> Find the signal in the noise. Move while the window is open.

Viral Waves watches the **micro-influencer layer** where trends start, automatically flagging:
- **Sounds** that surge among small accounts hours before they saturate
- **Formats** that jump between niches overnight  
- **Hashtag clusters** forming around styles that didn't exist 48 hours ago
- **Visual patterns** appearing across videos before they're recognized as trends

### How It Works (Conceptual)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         VIRAL WAVES SYSTEM                               │
├─────────────────────────────────────────────────────────────────────────┤
│  DATA COLLECTION          TREND DETECTION              ALERT DELIVERY   │
│                                                                          │
│  ┌──────────────┐        ┌──────────────┐         ┌─────────────────┐  │
│  │ TikTok Data  │───────▶│ Growth Rate  │────────▶│  SMS / Email    │  │
│  │ Sources      │        │ Analysis     │         │  Slack / Discord│  │
│  └──────────────┘        ├──────────────┤         └─────────────────┘  │
│                          │ Niche        │                                │
│                          │ Clustering   │                                │
│                          ├──────────────┤                                │
│                          │ Visual       │                                │
│                          │ Similarity   │                                │
│                          └──────────────┘                                │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Insight: Velocity > Volume

The mathematical insight that makes this work:

> A sound with 500 uses growing at 400% per hour is a better signal than one with 50,000 uses that peaked yesterday.

**Velocity metrics trump absolute volume** because:
- Exponential growth patterns are the strongest predictors of virality
- Early-stage detection requires monitoring growth rates, not just usage counts
- Acceleration (second derivative) indicates a trend's momentum phase

---

## Market Validation & Timing

### Search Trend Data

The keyword "viral trending video" shows explosive demand:

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Search Volume** | 6,600/month | Significant baseline interest |
| **Growth** | **+4,614%** | Massive, recent spike in demand |

This 46x growth in search interest indicates:
- Market awareness of the problem is skyrocketing
- Creators are actively seeking solutions
- First-mover advantage window is open

### Why Now?

| Factor | Status |
|--------|--------|
| **Short-form video boom** | TikTok + Reels + Shorts have trained audiences to expect constant novelty |
| **AI capabilities** | Computer vision and NLP now make automated trend detection feasible |
| **Creator economy maturity** | Professional creators need professional tools; manual methods don't scale |
| **Unmet need** | No existing tool specifically addresses *early-stage* TikTok trend detection |

### Competitive Landscape

| Competitor | Gap Viral Waves Fills |
|------------|----------------------|
| **Adobe (Creative Cloud)** | No real-time trend detection; focused on creation tools |
| **Native TikTok Analytics** | Backward-looking; doesn't predict emerging trends |
| **General social listening tools** | Too slow; not TikTok-native; miss micro-trends |
| **Influencer platforms** | Focus on established creators, not trend origination |

---

## Target Users & Use Cases

### Primary Segments

| Segment | Needs | Value Received |
|---------|-------|----------------|
| **Solo Creators ($29/month)** | Personal brand growth, more views, less scrolling | 4 hours of scrolling becomes one notification |
| **Agencies ($199/month)** | Client trend reports, competitive advantage, scalability | Stop assigning someone to scroll; automate research |
| **Enterprise ($499/month)** | Multi-account management, team collaboration, API access | Centralized trend intelligence for content teams |

### User Journeys

**Scenario 1: Solo Creator**
1. Creator receives Slack alert: "Sound 'XYZ' surging 340% in beauty niche"
2. Alert includes: usage graph, similar videos, suggested script angle
3. Creator films video using sound within 2 hours
4. Video rides the trend wave, achieves 10x normal views

**Scenario 2: Creative Agency**
1. Agency managing 15 client accounts receives morning trend digest
2. Identifies 3 cross-niche format trends applicable to client verticals
3. Briefs content team with trend context and execution guidance
4. Clients' content calendars updated with trending formats before competitors

---

## Product Vision & Roadmap

### MVP Phase (Launch)

**Core Features:**
- **TikTok-only** trend detection (sounds, hashtags, formats)
- Multi-region coverage from day one
- **Tier-based alert system:**
  - **Free:** Weekly digest, basic alerts, Slack/Email only
  - **Solo ($29/mo):** 2-hour latency, detailed alerts, Slack/Email
  - **Agency ($199/mo):** 30-minute latency, white-label reports, Slack/Email
  - **Enterprise ($499/mo):** Real-time alerts, SMS included, API access
- Growth rate threshold monitoring
- Basic niche clustering

**Success Metric:** 50 creators actively using and iterating based on alerts

### Growth Phase (Months 3-6)

**Expanded Features:**
- Script suggestions based on trend context
- Competitor tracking (what's working for similar creators)
- Viral prediction scores
- Visual similarity detection for format trends

### Scale Phase (Months 6-12)

**Platform Expansion:**
- ~~Instagram Reels integration~~ (Not planned - TikTok focus)
- ~~YouTube Shorts integration~~ (Not planned - TikTok focus)
- Cross-platform trend correlation (if expansion pursued later)
- Advanced API for enterprise integrations
- Enhanced white-label capabilities for MCNs and talent agencies

---

## Success Criteria

### Short-Term (3 months)
- [ ] 100 paying subscribers
- [ ] >70% monthly active usage
- [ ] User-reported "trend wins" (creators crediting alerts for viral content)
- [ ] <5 minute average time from trend detection to user alert

### Medium-Term (6 months)
- [ ] 1,000 paying subscribers across all tiers
- [ ] 50+ agency clients
- [ ] Predictive accuracy: >60% of flagged trends achieve >100K uses
- [ ] Expansion to 2 additional platforms

### Long-Term (12 months)
- [ ] Become the "Bloomberg Terminal" for short-form video trends
-- [ ] 10,000+ active users
- [ ] Integration partnerships with major creator tools
- [ ] White-label offering for MCNs and talent agencies

---

## Open Questions for Clarification

To refine this intent document, the following questions should be answered:

### Product Scope
1. ✅ **Geographic Focus:** Multi-region from day one. Algorithms optimized for global trend detection.
2. **Niche Coverage:** Are there specific verticals (beauty, finance, comedy) we should prioritize?
3. ✅ **Alert Frequency:** Tier-based approach:
   - **Free Tier:** Weekly digest (proof of concept, limited utility)
   - **Solo ($29/mo):** 2-hour latency alerts (Slack/Email only)
   - **Agency ($199/mo):** 30-minute latency alerts
   - **Enterprise ($499/mo):** Real-time alerts (including SMS)

### Business Model
4. ✅ **Free Tier:** Yes - weekly digest with basic alerts (proof the service works, but limited utility). No SMS (cost control). Paid tiers get progressively more detailed reports and faster alerts.
5. **Data Retention:** How much historical trend data should users have access to?
6. ✅ **White-label:** Near-term priority - Agency tier ($199/mo) includes white-label capabilities

### Technical Priorities
7. ✅ **Platform Priority:** TikTok ONLY for MVP. No expansion to other platforms envisioned at this stage.
8. **Visual Analysis:** Is visual similarity detection required for MVP or can it come later?
9. ✅ **Real-time vs Near Real-time:** Tier-based latency:
   - Free: Weekly digest
   - Solo: 2-hour latency
   - Agency: 30-minute latency
   - Enterprise: Real-time (< 5 min)

### Competitive Differentiation
10. **Community Features:** Should we build creator community features or stay purely tool-focused?
11. **Script Generation:** How automated should script suggestions be?
12. **Education:** Do users need trend education or just raw alerts?

---

## Summary

Viral Waves addresses a **genuine, validated pain point** in the creator economy. The +4,614% search growth for "viral trending video" confirms market demand. The technical approach—monitoring velocity at the micro-influencer layer—provides a defensible methodology that general social listening tools cannot easily replicate.

The opportunity window is open. Speed wins on TikTok, and the tool that gives creators that speed will capture significant value.

---

*Document Version: 1.0*  
*Last Updated: 2026-02-16*  
*Next Review: Upon technical feasibility assessment completion*
