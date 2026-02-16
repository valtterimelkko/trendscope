---
name: seo-content-planner
description: Create a content strategy with pillar pages, topic clusters, and content calendar. Maps keywords to funnel stages and applies Business Potential scoring.
invocation: Use when Phase 1.4.6 begins, after keyword research (1.4.2) and brand voice codification (1.4.5) are complete.
location: project
---

# SEO Content Planner

## Purpose

Transform keyword research into an actionable content strategy. This skill creates the architecture for sustainable organic growth by mapping content to buyer journey stages and prioritizing by business impact.

## Prerequisites

Before running this skill, ensure:
- `marketing/keyword-research.md` exists (REQUIRED - from Phase 1.4.2)
- `marketing/positioning-angles.md` exists (from Phase 1.4.1)
- `docs/concept/master-concept.md` exists
- `docs/brand/brand-kit-guide.md` has Voice Codification section (from Phase 1.4.5)

## External Signals

This skill uses trend data to inform content timing:

### pytrends (No API key needed)
- Script: `.claude/scripts/marketing/trend_signals.py`
- Provides: Rising queries for content opportunities

## Output

Creates: `marketing/seo-content.md`

## Process

### Phase 1: Content Architecture (Pillar-Cluster Model)

#### Identify Pillars

From keyword research, identify 3-5 "pillar" topics:

- High search volume (relative to your niche)
- Broad enough to support 5-10 cluster articles
- Directly related to your product's value proposition

```markdown
## Pillar: [Topic Name]

**Target Keyword:** [main keyword]
**Search Intent:** [informational/commercial/navigational]
**Content Type:** Comprehensive guide (2000-3000 words)
**URL Path:** /guides/[topic]

**Cluster Topics:**
1. [Subtopic 1] → targets: [keyword]
2. [Subtopic 2] → targets: [keyword]
3. [Subtopic 3] → targets: [keyword]
...
```

#### Design Cluster Structure

For each pillar, map supporting content:

```
[Pillar Page: "Complete Guide to X"]
    ├── [Cluster 1: "How to Y"]
    ├── [Cluster 2: "X vs Z Comparison"]
    ├── [Cluster 3: "Best Practices for X"]
    ├── [Cluster 4: "X for [Industry]"]
    └── [Cluster 5: "Common X Mistakes"]
```

**Internal Linking Rules:**
- Every cluster links back to pillar
- Pillar links to all clusters
- Related clusters interlink
- Use keyword-rich anchor text (not "click here")

### Phase 2: Funnel Stage Mapping

Map all content to buyer journey stages:

#### ToFu (Top of Funnel) - Awareness

**User Intent:** Learning about the problem/space
**Keywords:** "what is", "how to", "guide to", "[topic] explained"
**Content Types:**
- Educational blog posts
- Beginner guides
- Industry reports
- Glossaries/definitions

**Conversion Goal:** Email capture, resource download
**Metrics:** Traffic, time on page, email signups

#### MoFu (Middle of Funnel) - Consideration

**User Intent:** Evaluating solutions
**Keywords:** "best [category]", "[product] vs [product]", "alternatives to"
**Content Types:**
- Comparison pages
- "Best of" listicles
- Case studies
- Webinars

**Conversion Goal:** Demo request, trial signup
**Metrics:** Qualified leads, demo requests

#### BoFu (Bottom of Funnel) - Decision

**User Intent:** Ready to buy, final research
**Keywords:** "[product] pricing", "[product] review", "buy [product]"
**Content Types:**
- Pricing pages
- ROI calculators
- Customer testimonials
- Integration guides

**Conversion Goal:** Purchase, trial-to-paid
**Metrics:** Revenue, conversion rate

### Phase 3: Business Potential Scoring

Apply Ahrefs-style Business Potential score (0-3):

| Score | Definition | Example |
|-------|------------|---------|
| **3** | Product is irreplaceable solution | "how to automate billing" for billing software |
| **2** | Product helps significantly | "subscription management best practices" |
| **1** | Product can be mentioned naturally | "SaaS metrics to track" |
| **0** | No natural product tie-in | General industry news |

**Prioritization Rule:** Focus 70% of content on Score 2-3 topics.

### Phase 4: Content Calendar Creation

#### Quarter 1 Priority (Months 1-3)

Focus on BoFu and high-potential MoFu:

| Week | Content Type | Title | Target Keyword | BP Score | Funnel |
|------|-------------|-------|----------------|----------|--------|
| 1 | Landing | [Product] vs [Competitor] | [keyword] | 3 | BoFu |
| 2 | Blog | How to [Core Use Case] | [keyword] | 3 | MoFu |
| 3 | Blog | [N] Best [Category] Tools | [keyword] | 2 | MoFu |
| 4 | Pillar | Complete Guide to [Topic] | [keyword] | 2 | ToFu |
| ... | | | | | |

#### Month 1 Detail

```markdown
### Week 1
**Content:** [Title]
**Type:** [Blog/Landing/Pillar]
**Keywords:** Primary: [X], Secondary: [Y, Z]
**Word Count:** [target]
**Owner:** [AI Draft / Human Review]
**Internal Links To:** [existing pages]
**Internal Links From:** [planned future pages]
**CTA:** [what action]
**Status:** [ ] Outline → [ ] Draft → [ ] Edit → [ ] Publish

### Week 2
[Same structure]
```

### Phase 5: E-E-A-T Strategy

Plan for Experience, Expertise, Authoritativeness, Trustworthiness:

#### Experience
- Include first-hand examples and case studies
- Document actual product usage scenarios
- Share real metrics and results

#### Expertise
- Author bios with relevant credentials
- Expert quotes or contributions
- Depth of coverage (not surface-level)

#### Authoritativeness
- Earn backlinks from industry sites
- Get cited by other publications
- Build author profiles on industry platforms

#### Trustworthiness
- Clear About page with team info
- Visible contact information
- Privacy policy and terms
- Regular content updates

### Phase 6: Programmatic SEO Opportunities

Identify scalable content opportunities:

#### Template Pages
If product has templates/integrations:

```markdown
## Programmatic Opportunity: Templates

**URL Pattern:** /templates/[use-case]
**Example:** /templates/project-management, /templates/crm

**Page Structure:**
- H1: [Use Case] Template
- Description of use case
- Template preview/demo
- "Use This Template" CTA
- Related templates

**Keywords Targeted:**
- "[use case] template"
- "free [use case] template"
- "[use case] spreadsheet"

**Scale:** [N] pages possible
```

#### Integration Pages
If product integrates with other tools:

```markdown
## Programmatic Opportunity: Integrations

**URL Pattern:** /integrations/[tool-a]-[tool-b]
**Example:** /integrations/slack-google-sheets

**Page Structure:**
- H1: Connect [Tool A] to [Tool B]
- What you can automate
- Setup steps
- Common use cases

**Keywords Targeted:**
- "[tool a] [tool b] integration"
- "connect [tool a] to [tool b]"
- "[tool a] [tool b] automation"
```

### Phase 7: Trend-Based Content Timing

Run trend analysis for content timing:

```bash
python .claude/scripts/marketing/trend_signals.py \
  --keywords "keyword1,keyword2,keyword3" \
  --timeframe "today 12-m"
```

#### Rising Topics (Prioritize)
Content targeting rising queries should be created/published early to capture growth.

#### Seasonal Topics
Identify seasonal patterns and plan content 1-2 months before peaks.

#### Declining Topics
Deprioritize or avoid unless strategic reason exists.

### Phase 8: Technical SEO Checklist

Ensure content can be discovered:

```markdown
## Technical SEO Requirements

### Per-Page Requirements
- [ ] Unique, keyword-rich title tag (50-60 chars)
- [ ] Meta description with CTA (150-160 chars)
- [ ] H1 matches target keyword intent
- [ ] H2/H3 structure uses secondary keywords
- [ ] Images have descriptive alt text
- [ ] Internal links to related content
- [ ] External links to authoritative sources
- [ ] Schema markup (Article, FAQ, HowTo as appropriate)

### Site-Wide Requirements
- [ ] XML sitemap generated and submitted
- [ ] Robots.txt allows crawling
- [ ] Canonical tags on all pages
- [ ] Mobile-responsive design
- [ ] Page speed < 3 seconds
- [ ] HTTPS enabled
- [ ] Breadcrumb navigation
```

## Output Template

```markdown
# SEO Content Strategy - [Product Name]

Generated: [Date]
Based on: keyword-research.md, positioning-angles.md, master-concept.md

## Executive Summary

- Total content pieces planned: [N]
- Pillars identified: [N]
- BoFu priority pieces: [N]
- Estimated monthly traffic potential: [range]

---

## Content Architecture

### Pillar 1: [Topic]
[Full structure with clusters]

### Pillar 2: [Topic]
[Full structure with clusters]

### Pillar 3: [Topic]
[Full structure with clusters]

---

## Funnel Stage Distribution

| Stage | Content Pieces | Primary Keywords |
|-------|---------------|------------------|
| ToFu | [N] | [list] |
| MoFu | [N] | [list] |
| BoFu | [N] | [list] |

---

## Business Potential Prioritization

### Score 3 (Product Essential)
[List with target keywords]

### Score 2 (Product Helpful)
[List with target keywords]

### Score 1 (Brand Awareness)
[List with target keywords]

---

## Content Calendar

### Month 1
[Detailed weekly plan]

### Month 2
[Weekly plan]

### Month 3
[Weekly plan]

---

## Programmatic SEO Opportunities

[Template pages, integration pages, etc.]

---

## Trend Insights

### Rising Topics (Create Now)
[From trend_signals.py]

### Seasonal Considerations
[Timing notes]

---

## E-E-A-T Strategy

[Experience, Expertise, Authority, Trust plan]

---

## Technical Requirements

[Checklist]

---

## Success Metrics

| Metric | Month 1 Target | Month 3 Target | Month 6 Target |
|--------|---------------|----------------|----------------|
| Organic Traffic | [X] | [X] | [X] |
| Keyword Rankings (Top 10) | [N] | [N] | [N] |
| Backlinks | [N] | [N] | [N] |
| Demo Requests from Organic | [N] | [N] | [N] |

---

## Next Steps

1. Begin with BoFu content (highest conversion impact)
2. Build pillar pages to establish topical authority
3. Create cluster content to support pillars
4. Monitor rankings and iterate on underperforming content
5. Revisit quarterly with fresh keyword research
```

## Quality Checklist

Before completing, verify:
- [ ] Keyword research document thoroughly analyzed
- [ ] Identified 3-5 pillar topics with clusters
- [ ] All content mapped to funnel stages
- [ ] Applied Business Potential scoring
- [ ] Created detailed Month 1 calendar
- [ ] Outlined Months 2-3
- [ ] Identified programmatic SEO opportunities
- [ ] Included E-E-A-T strategy
- [ ] Defined technical SEO requirements
- [ ] Set measurable success metrics
