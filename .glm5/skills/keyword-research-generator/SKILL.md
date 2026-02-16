---
name: keyword-research-generator
description: Build a strategic keyword map using the 6 Circles Method with API signals from Google Ads and pytrends. Creates prioritized keyword list for SEO and content strategy.
invocation: Use when Phase 1.4.2 begins, after positioning angles are complete.
location: project
---

# Keyword Research Generator

## Purpose

Build a comprehensive keyword map that identifies high-intent search terms for the MVP. Uses the "6 Circles Method" to systematically discover keywords from multiple sources, then prioritizes using the RevenueZen matrix.

## Prerequisites

Before running this skill, ensure:
- `docs/concept/master-concept.md` exists (JTBD, problem statements)
- `marketing/positioning-angles.md` exists (from Phase 1.4.1)

**Optional (if available):**
- `docs/mvp-ux-*.md` (user journeys, feature names) - only available if revisiting after Phase 2.1

## External Signals

This skill uses helper scripts to fetch external data:

### Google Ads API (Optional)
- Provides: Search volume, CPC, competition level
- Script: `.claude/scripts/marketing/keyword_signals.py`
- Env: `GOOGLE_ADS_DEVELOPER_TOKEN`

### pytrends (No API key needed)
- Provides: Trend velocity, rising queries, related terms
- Script: `.claude/scripts/marketing/trend_signals.py`

### Autosuggest Scraping (No API key needed)
- Provides: Google/Bing autocomplete suggestions
- Script: `.claude/scripts/marketing/autosuggest.py`

## Output

Creates: `marketing/keyword-research.md`

## Process

### Phase 1: Seed Term Extraction (Circle 1 - Your Knowledge)

Extract seed terms from existing documents:

1. From **Master Concept**:
   - Problem statements (pain points)
   - JTBD functional jobs
   - Product category terms
   - Feature names

2. From **Positioning Angles**:
   - Category terms used
   - Competitor names mentioned
   - Outcome phrases

3. From **UX Spec**:
   - Feature names
   - User action verbs
   - Workflow terminology

Create initial seed list of 10-20 terms.

### Phase 2: Audience Query Mining (Circle 2 - Your Audience)

Generate problem-aware queries using JTBD patterns:

**Functional Job Queries:**
- "how to [job]"
- "[job] software"
- "[job] tool"
- "best way to [job]"

**Emotional Job Queries:**
- "frustrated with [pain]"
- "tired of [pain]"
- "[pain] solution"

**Social Job Queries:**
- "[role] tools"
- "what do [roles] use for [task]"

### Phase 3: Competitor Intelligence (Circle 3 - Competitors)

For each competitor identified in Master Concept:

1. Analyze their sitemap (manual or via script):
   ```
   https://competitor.com/sitemap.xml
   ```

2. Extract:
   - Blog post titles/URLs
   - Feature page names
   - Integration page names

3. Identify keyword patterns they target

### Phase 4: Market Taxonomy (Circle 4 - Market)

Build category taxonomy:

```
[Primary Category]
├── [Subcategory A]
│   ├── [Term 1]
│   └── [Term 2]
├── [Subcategory B]
│   ├── [Term 3]
│   └── [Term 4]
```

Include:
- Industry terms
- Process terms
- Role-specific terms

### Phase 5: Trend Signals (Circle 5 - Trends)

Run the trend signals script:

```bash
python .claude/scripts/marketing/trend_signals.py --keywords "keyword1,keyword2,keyword3"
```

The script returns:
- Interest over time (growing/declining)
- Rising related queries
- Top related queries
- Regional interest data

Flag keywords that are:
- **Rising (>100% growth)** - Priority opportunities
- **Declining** - Avoid or deprioritize
- **Stable** - Safe, predictable traffic

### Phase 6: Opportunity Discovery (Circle 6 - Opportunities)

Run autosuggest expansion:

```bash
python .claude/scripts/marketing/autosuggest.py --seed "keyword"
```

This mines:
- Google autocomplete
- "People Also Ask" patterns
- Alphabetic variations (keyword a, keyword b, ...)

Identify:
- Long-tail variations
- Question-based queries
- Problem-solution phrases

### Phase 7: Keyword Enrichment (Optional API)

If `GOOGLE_ADS_DEVELOPER_TOKEN` is available:

```bash
python .claude/scripts/marketing/keyword_signals.py --keywords "keyword1,keyword2" --action volume
```

Returns:
- Monthly search volume
- Competition level (LOW/MEDIUM/HIGH)
- Suggested bid (CPC indicator)

If API unavailable, use qualitative assessment based on:
- Autosuggest presence (indicates volume)
- SERP competition (manual check)
- Trend velocity from pytrends

### Phase 8: Prioritization Matrix

Score each keyword using RevenueZen matrix:

| Criteria | Weight | 1 (Low) | 2 (Medium) | 3 (High) |
|----------|--------|---------|------------|----------|
| **Search Volume** | 20% | <100/mo | 100-1000/mo | >1000/mo |
| **Intent Signal** | 35% | Informational | Commercial | Transactional |
| **Competition** | 25% | High (DR>50) | Medium (DR 20-50) | Low (DR<20) |
| **Business Fit** | 20% | Tangential | Related | Core offering |

**Intent Classification:**
- **Informational:** "what is [topic]", "how does [topic] work"
- **Commercial:** "best [category]", "[product] vs [product]", "[product] reviews"
- **Transactional:** "[product] pricing", "buy [product]", "[product] free trial"

### Phase 9: Keyword Clustering

Group keywords into clusters for content planning:

```markdown
## Cluster: [Topic]

**Pillar Keyword:** [main term]
**Search Volume:** [X]/mo
**Intent:** [type]

**Supporting Keywords:**
- [variation 1] - [volume]
- [variation 2] - [volume]
- [variation 3] - [volume]

**Content Opportunity:**
- Type: [blog post / landing page / comparison page]
- Funnel Stage: [ToFu / MoFu / BoFu]
```

## Output Template

```markdown
# Keyword Research - [Product Name]

Generated: [Date]
Based on: master-concept.md, positioning-angles.md, mvp-ux-*.md
API Status: [Google Ads: Available/Unavailable] | [pytrends: Available]

## Executive Summary

- Total keywords identified: [N]
- High-priority keywords: [N]
- Primary clusters: [N]
- Recommended immediate targets: [list top 5]

---

## Seed Terms

### From Master Concept
[List]

### From Positioning
[List]

### From UX Spec
[List]

---

## Keyword Clusters

### Cluster 1: [Topic Name]

| Keyword | Volume | Intent | Competition | Business Fit | Priority Score |
|---------|--------|--------|-------------|--------------|----------------|
| [term]  | [X]    | [type] | [level]     | [score]      | [X/100]        |

**Content Recommendation:** [type and angle]

[Repeat for each cluster]

---

## Trend Analysis

### Rising Opportunities
| Keyword | Growth Rate | Current Interest |
|---------|-------------|------------------|
| [term]  | +X%         | [0-100]          |

### Declining Terms (Avoid)
| Keyword | Decline Rate |
|---------|--------------|
| [term]  | -X%          |

---

## Competitor Keyword Gaps

Keywords competitors rank for that we should target:
[List with rationale]

---

## Priority Keyword List

### Tier 1 (Immediate - BoFu)
[5-10 transactional/commercial keywords]

### Tier 2 (Short-term - MoFu)
[10-15 commercial/comparison keywords]

### Tier 3 (Long-term - ToFu)
[15-20 informational keywords]

---

## Next Steps

1. Use Tier 1 keywords for landing page optimization
2. Use clusters for SEO Content Planner (Phase 1.4.6)
3. Monitor rising trends monthly
4. Revisit after 90 days of search console data
```

## Helper Script Usage

### trend_signals.py

```bash
# Get trend data for keywords
python .claude/scripts/marketing/trend_signals.py \
  --keywords "saas billing,subscription management,recurring payments" \
  --timeframe "today 12-m"

# Output: JSON with interest_over_time, related_queries, rising_queries
```

### autosuggest.py

```bash
# Expand seed keywords via autosuggest
python .claude/scripts/marketing/autosuggest.py \
  --seed "project management" \
  --depth 2

# Output: List of autocomplete suggestions
```

### keyword_signals.py (requires API)

```bash
# Get volume data (if API available)
python .claude/scripts/marketing/keyword_signals.py \
  --keywords "keyword1,keyword2" \
  --action volume

# Output: JSON with search_volume, competition, cpc
```

## Quality Checklist

Before completing, verify:
- [ ] Extracted seeds from all three source documents
- [ ] Applied 6 Circles Method systematically
- [ ] Ran trend signals script (or documented manual research)
- [ ] Clustered keywords by topic
- [ ] Classified intent for each keyword
- [ ] Prioritized using RevenueZen matrix
- [ ] Identified at least 3 Tier 1 (BoFu) keywords
- [ ] Documented data source limitations if API unavailable
