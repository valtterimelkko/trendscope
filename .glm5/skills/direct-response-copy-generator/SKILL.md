---
name: direct-response-copy-generator
description: Generate high-converting landing page and email copy using proven direct response frameworks (PAS, AIDA, BAB, JTBD). Produces ready-to-use copy blocks.
invocation: Use when Phase 1.4.4 begins, after positioning angles are defined.
location: project
---

# Direct Response Copy Generator

## Purpose

Generate conversion-focused copy for landing pages, emails, and ads using proven direct response frameworks. This skill translates positioning strategy into persuasive language that moves prospects to action.

## Prerequisites

Before running this skill, ensure:
- `docs/concept/master-concept.md` exists (JTBD, pain points)
- `docs/brand/brand-kit-guide.md` exists (voice attributes)
- `marketing/positioning-angles.md` exists (from Phase 1.4.1)

## Output

Creates: `marketing/direct-response-copy.md`

## Process

### Phase 1: Copywriting Foundation

#### Extract Voice Attributes
From Brand Kit, identify:
- Tone dimensions (Formal/Casual, Serious/Playful, etc.)
- Vocabulary preferences
- Sentence rhythm

#### Determine Awareness Level
Match copy approach to prospect awareness:

| Awareness | Copy Focus | Length |
|-----------|------------|--------|
| Unaware | Problem education | Long |
| Problem-Aware | Problem agitation → Solution | Medium-Long |
| Solution-Aware | Differentiation | Medium |
| Product-Aware | Features, proof, offer | Short |
| Most Aware | Offer, urgency | Very Short |

### Phase 2: Apply Copywriting Frameworks

#### Framework 1: PAS (Problem-Agitate-Solution)
Best for: Pain-killer products, problem-aware audience

```
PROBLEM: [State the problem they recognize]
AGITATE: [Twist the knife - consequences of not solving]
SOLUTION: [Your product as the relief]
```

Example:
- Problem: "Spending hours reconciling spreadsheets?"
- Agitate: "Every manual error costs you $X and damages client trust."
- Solution: "Automate your reconciliation in 3 clicks."

#### Framework 2: AIDA (Attention-Interest-Desire-Action)
Best for: Longer form content, building from awareness

```
ATTENTION: [Pattern interrupt, bold claim]
INTEREST: [Expand with specifics, data]
DESIRE: [Paint the transformation, social proof]
ACTION: [Clear CTA]
```

#### Framework 3: BAB (Before-After-Bridge)
Best for: Cold outreach, quick pitches

```
BEFORE: [Their current painful state]
AFTER: [Their ideal future state]
BRIDGE: [Your product as the path]
```

#### Framework 4: JTBD (Jobs-to-Be-Done)
Best for: Feature pages, use case content

```
WHEN [situation], I WANT TO [motivation], SO THAT [outcome].
```

#### Framework 5: 4 U's (Useful-Urgent-Unique-Ultra-specific)
Best for: Headlines, subject lines

Rate each headline 1-4 on each U, aim for 12+.

### Phase 3: Feature-Benefit-Emotion Ladder

Transform features into compelling copy:

```
FEATURE: [What it does technically]
    ↓
BENEFIT: [What that means for the user]
    ↓
EMOTION: [How that makes them feel]
```

Example:
- Feature: "Real-time sync across devices"
- Benefit: "Never lose work when switching between laptop and phone"
- Emotion: "Peace of mind that your work is always safe"

**Rule:** Lead with emotion, support with benefit, prove with feature.

### Phase 4: Generate Copy Blocks

#### Hero Section

```markdown
## Hero Section

**H1 (Primary Headline):**
[6-12 words, benefit-focused, applies positioning]

**H2 (Supporting Subheadline):**
[Clarify the offer, add specificity]

**Social Proof Snippet:**
[Micro-proof: "Trusted by X companies" or "4.8/5 from Y reviews"]

**Primary CTA:**
[Action verb + outcome: "Start Saving Time" not "Submit"]

**Secondary CTA:**
[Lower commitment: "See How It Works" or "View Demo"]

**Hero Visual Direction:**
[Guidance on what image/video should convey]
```

#### Problem Section

```markdown
## Problem Section

**Section Header:**
[Question that resonates: "Tired of X?"]

**Pain Points (3-4 bullets):**
- [Pain 1 with specific detail]
- [Pain 2 with consequence]
- [Pain 3 with emotional impact]
- [Pain 4 with status quo frustration]

**Agitation Paragraph:**
[2-3 sentences that make the problem feel urgent]
```

#### Solution Section (How It Works)

```markdown
## How It Works

**Section Header:**
[Promise simplicity: "3 Steps to [Outcome]"]

**Step 1:**
- Icon suggestion: [type]
- Headline: [Action verb phrase]
- Body: [1-2 sentences explaining]

**Step 2:**
- Icon suggestion: [type]
- Headline: [Action verb phrase]
- Body: [1-2 sentences explaining]

**Step 3:**
- Icon suggestion: [type]
- Headline: [Action verb phrase]
- Body: [1-2 sentences explaining]

**Result Statement:**
[What happens after step 3: "And just like that, you've [achieved outcome]"]
```

#### Features/Benefits Section

```markdown
## Features

**Section Header:**
[Value-focused: "Everything You Need to [Outcome]"]

**Feature 1:**
- Headline: [Benefit-first headline]
- Body: [2-3 sentences with specific capability]
- Proof: [Data point or testimonial snippet]

**Feature 2:**
[Same structure]

**Feature 3:**
[Same structure]
```

#### Social Proof Section

```markdown
## Social Proof

**Section Header:**
[Community-focused: "Join X+ Teams Who [Outcome]"]

**Testimonial 1:**
- Quote: "[Specific result achieved]"
- Attribution: [Name, Title, Company]
- Logo: [Company logo permission needed]

**Testimonial 2:**
[Same structure - different persona if possible]

**Metrics Bar:**
- Stat 1: [X+ Users/Companies]
- Stat 2: [X% Improvement Achieved]
- Stat 3: [X Hours Saved / X$ Generated]

**Logo Cloud:**
[List 4-8 recognizable customer logos]
```

#### FAQ Section

```markdown
## FAQ

**Objection 1: [Price concern]**
Q: [Common pricing question]
A: [Value reframe + comparison to alternatives/cost of problem]

**Objection 2: [Complexity concern]**
Q: [Setup/learning curve question]
A: [Ease of use proof + support availability]

**Objection 3: [Risk concern]**
Q: [Security/reliability question]
A: [Trust signals + guarantees]

**Objection 4: [Fit concern]**
Q: [Will this work for my use case?]
A: [Flexibility + specific use case examples]
```

#### Final CTA Section

```markdown
## Final CTA

**Headline:**
[Urgency or summary: "Ready to [Outcome]?"]

**Value Reminder:**
[1 sentence recap of transformation]

**CTA Button:**
[Same as hero, reinforced]

**Risk Reversal:**
[Guarantee, free trial, no credit card required]

**Microcopy Under Button:**
[Address final objection: "No credit card required" or "Cancel anytime"]
```

### Phase 5: Email Sequences

#### Onboarding Welcome Sequence

```markdown
## Onboarding Sequence

**Email 1: Welcome (Immediate)**
- Subject: [Welcome + immediate value]
- Body: Thank you, here's your first step, what to expect
- CTA: Complete first action

**Email 2: Quick Win (Day 1)**
- Subject: [Curiosity + value]
- Body: Show them one powerful feature/tip
- CTA: Try this feature

**Email 3: Social Proof (Day 3)**
- Subject: [Story hook]
- Body: Customer success story relevant to their use case
- CTA: See more success stories

**Email 4: Value Expansion (Day 5)**
- Subject: [Did you know...]
- Body: Highlight underused feature
- CTA: Explore feature

**Email 5: Feedback Request (Day 7)**
- Subject: [Question format]
- Body: Ask for feedback, offer help
- CTA: Reply or schedule call
```

#### Cold Outreach Sequence

```markdown
## Cold Outreach Sequence

**Email 1: Initial Touch**
- Subject: [6 words max, curiosity or relevance]
- Body: [3-4 sentences max]
  - Line 1: Relevance hook (why them)
  - Line 2: Value prop (one sentence)
  - Line 3: Social proof (one data point)
  - Line 4: Soft ask (reply/quick call)

**Email 2: Follow-up (Day 3)**
- Subject: Re: [previous] or [new angle]
- Body: Add new information or angle
- CTA: Same ask, different frame

**Email 3: Breakup (Day 7)**
- Subject: [Closing the loop]
- Body: Acknowledge busy, final value point, leave door open
- CTA: Reply if interested, no pressure
```

### Phase 6: We-We Audit

**Critical check:** Count "we/our" vs "you/your" in all copy.

- Target ratio: 3:1 (you:we) or higher
- Every "we" should serve the reader's interest

Before:
> "We built the fastest analytics platform. Our team has 20 years experience."

After:
> "Get insights 10x faster. You're backed by a team with 20 years experience."

## Output Template

```markdown
# Direct Response Copy - [Product Name]

Generated: [Date]
Based on: master-concept.md, brand-kit-guide.md, positioning-angles.md

## Copy Strategy

**Target Awareness:** [Level]
**Primary Framework:** [PAS/AIDA/BAB]
**Voice Profile:** [Key attributes from Brand Kit]
**Positioning Angle:** [From positioning-angles.md]

---

## Landing Page Copy

### Hero Section
[Full copy block]

### Problem Section
[Full copy block]

### Solution Section
[Full copy block]

### Features Section
[Full copy block]

### Social Proof Section
[Full copy block]

### FAQ Section
[Full copy block]

### Final CTA Section
[Full copy block]

---

## Email Sequences

### Onboarding Sequence
[Full sequence]

### Cold Outreach Sequence
[Full sequence]

---

## Ad Copy Variants

### Google Ads
- Headline 1 (30 char): [copy]
- Headline 2 (30 char): [copy]
- Headline 3 (30 char): [copy]
- Description 1 (90 char): [copy]
- Description 2 (90 char): [copy]

### LinkedIn Ads
- Intro text (150 char): [copy]
- Headline (70 char): [copy]
- CTA: [button choice]

---

## Headline Variants for A/B Testing

1. [Benefit-focused variant]
2. [Social proof variant]
3. [Curiosity variant]
4. [Urgency variant]
5. [Specificity variant]

---

## Quality Metrics

- We-We Ratio: [X:Y] (target 3:1 you:we)
- Flesch Reading Ease: [score] (target 60+)
- Average Sentence Length: [X words] (target <20)

---

## Next Steps

1. Review with brand voice (Phase 1.4.5) for tone consistency
2. Integrate keywords from keyword-research.md
3. A/B test headline variants
4. Customize for specific landing pages during development
```

## Anti-Patterns to Avoid

1. **Feature Dumping** - Listing features without benefits
2. **Corporate Speak** - "Leverage", "Synergy", "Best-in-class"
3. **Weak CTAs** - "Submit", "Click Here", "Learn More"
4. **No Specificity** - Vague claims without numbers or details
5. **Ignoring Objections** - Not addressing why they might say no
6. **Long Paragraphs** - More than 3-4 sentences per paragraph

## Quality Checklist

Before completing, verify:
- [ ] Identified target awareness level
- [ ] Applied appropriate framework (PAS/AIDA/BAB)
- [ ] Transformed features into benefits and emotions
- [ ] Generated all copy blocks for landing page
- [ ] Created onboarding and cold outreach sequences
- [ ] Passed We-We audit (3:1 ratio)
- [ ] Included specific numbers and proof points
- [ ] Provided headline variants for testing
- [ ] Aligned with brand voice attributes
