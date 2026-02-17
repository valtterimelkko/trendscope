---
name: positioning-angles-generator
description: Generate strategic positioning angles for MVP products using 8 proven frameworks. Produces 3-5 positioning candidates with headlines ready for smoke testing.
invocation: Use when Phase 1.4.1 begins, after Master Concept and Brand Kit are complete.
location: project
---

# Positioning Angles Generator

## Purpose

Generate strategic positioning angles that define the market context for an MVP. Positioning is the "strategic bedrock" that determines how customers categorize and value the product. This skill produces multiple positioning candidates for validation.

## Prerequisites

Before running this skill, ensure these documents exist:
- `docs/concept/master-concept.md` - Contains problem, audience, JTBD, competitive alternatives
- `docs/brand/brand-kit-guide.md` - Contains brand personality archetype

## Output

Creates: `marketing/positioning-angles.md`

## Process

### Phase 1: Extract Strategic Inputs

Read the Master Concept and extract:

1. **Competitive Alternatives** - What does the customer do today if your product doesn't exist?
   - Direct competitors (similar software)
   - Indirect alternatives (spreadsheets, manual processes, hiring)
   - Status quo (do nothing)

2. **Jobs-to-Be-Done (JTBD)** - The functional, emotional, and social jobs

3. **Target Audience** - Primary persona with their specific context

4. **Unique Attributes** - What can you do that alternatives cannot?

### Phase 2: Apply Positioning Frameworks

Generate positioning angles using these 8 frameworks:

#### Framework 1: Category Positioning
- Define a new category or reframe an existing one
- Template: "We are not [Old Category]; we are the world's first [New Category]"
- Best when: Product innovation is radical, existing category has negative connotations

#### Framework 2: Comparative Positioning (Anti-Position)
- Position against a named incumbent's weakness
- Template: "The [Competitor] alternative for [specific audience]" or "Unlike [Competitor], we focus on [strength]"
- Best when: Entering crowded market with frustrated users

#### Framework 3: Audience-First Positioning
- Focus on WHO, not WHAT
- Template: "The only [category] built specifically for [audience]"
- Best when: Technology is commoditized but application to segment is unique

#### Framework 4: Outcome-Based Positioning
- Sell the transformation, not features
- Template: "Don't buy software; buy [outcome]"
- Best when: Mature market where features are table stakes

#### Framework 5: Value-Stack Positioning
- Highlight tool consolidation
- Template: "Replace [Tool A], [Tool B], and [Tool C] with one unified platform"
- Best when: Market is fragmented, users suffer tool fatigue

#### Framework 6: Vertical/Industry Positioning
- Target specific industry needs (compliance, integrations)
- Template: "The compliance-ready [category] for [industry]"
- Best when: Highly regulated industries (HealthTech, FinTech, LegalTech)

#### Framework 7: Price/Democratization Positioning
- Make enterprise capability accessible
- Template: "Professional-grade [capability] without the enterprise price tag"
- Best when: Incumbents are bloated, expensive, gate-kept by sales teams

#### Framework 8: Behavioral/Methodology Positioning
- Position around a philosophy or way of working
- Template: "The tool for teams who work [methodology]"
- Best when: Founders have strong opinions on HOW work should be done

### Phase 3: Generate Positioning Candidates

For each applicable framework, create a positioning candidate with:

```markdown
## Positioning Angle [N]: [Framework Name]

**Positioning Statement:**
For [target customer] who [statement of need], [product name] is a [market category] that [key benefit]. Unlike [competitive alternative], our product [primary differentiation].

**Headline Variants (for smoke testing):**
1. [6-10 word headline - benefit focused]
2. [6-10 word headline - audience focused]
3. [6-10 word headline - differentiation focused]

**Competitive Frame:**
- Positions against: [competitor/alternative]
- Our advantage: [specific strength]
- Their weakness: [specific gap we exploit]

**Best-Fit Customer:**
- Role: [job title/function]
- Trigger: [what makes them search for a solution]
- Success metric: [how they measure value]

**Risk Assessment:**
- Strengths: [why this angle could win]
- Weaknesses: [potential pitfalls]
- Validation needed: [what to test]
```

### Phase 4: Prioritize and Recommend

Score each positioning angle on:

| Criteria | Weight | Description |
|----------|--------|-------------|
| Differentiation | 30% | How clearly does it separate us from alternatives? |
| Relevance | 25% | How well does it match the target audience's language? |
| Credibility | 20% | Can we actually deliver on this promise? |
| Defensibility | 15% | How hard is it for competitors to copy this position? |
| Memorability | 10% | How sticky is the positioning? |

Provide a ranked recommendation with rationale.

### Phase 5: Smoke Test Plan

For the top 2-3 angles, define a validation plan:

```markdown
## Smoke Test Plan

### Landing Page A/B Test
- Variant A: [Headline from Angle 1]
- Variant B: [Headline from Angle 2]
- Variant C: [Headline from Angle 3]
- Traffic source: [LinkedIn Ads / Google Ads / Cold Email]
- Budget: $100-200
- Success metric: CTR > 1% (LinkedIn) or > 2% (Google)

### Cold Outreach Test
- Message: "I'm building [value prop]. Would you be interested?"
- Target: 50-100 prospects matching ICP
- Success metric: >10% positive reply rate
```

## Output Template

The final `marketing/positioning-angles.md` should follow this structure:

```markdown
# Positioning Angles - [Product Name]

Generated: [Date]
Based on: master-concept.md, brand-kit-guide.md

## Executive Summary

[2-3 sentence summary of the recommended positioning approach]

## Strategic Inputs

### Competitive Alternatives
[List from Master Concept]

### Jobs-to-Be-Done
[JTBD from Master Concept]

### Target Audience
[Primary persona]

### Unique Attributes
[Key differentiators]

---

## Positioning Candidates

[3-5 positioning angles using template above]

---

## Prioritization Matrix

| Angle | Differentiation | Relevance | Credibility | Defensibility | Memorability | Total |
|-------|-----------------|-----------|-------------|---------------|--------------|-------|
| 1     | X/10            | X/10      | X/10        | X/10          | X/10         | X/100 |

---

## Recommendation

**Primary Positioning:** [Angle N]
**Rationale:** [Why this wins]

**Secondary Positioning:** [Angle M]
**Use case:** [When to use this alternative angle]

---

## Validation Plan

[Smoke test plan as above]

---

## Next Steps

1. Run smoke tests on top 2-3 angles
2. Proceed to keyword research (Phase 1.4.2) using winning angle
3. Revisit positioning after customer discovery interviews
```

## Anti-Patterns to Avoid

1. **"AI-Washing"** - Don't lead with "AI-powered". Position on outcomes AI enables.
2. **"We Serve Everyone"** - Pick a beachhead segment. Win it completely first.
3. **Copying Competitors** - Define AGAINST them, not AS them.
4. **Feature Laundry Lists** - Positioning is context, not capabilities.
5. **Generic Claims** - "Best-in-class", "Next-gen", "Seamless" mean nothing.

## Quality Checklist

Before completing, verify:
- [ ] Read Master Concept and Brand Kit thoroughly
- [ ] Generated at least 3 distinct positioning angles
- [ ] Each angle has headline variants for testing
- [ ] Scored angles using prioritization matrix
- [ ] Provided clear recommendation with rationale
- [ ] Defined smoke test validation plan
- [ ] Avoided anti-patterns listed above
