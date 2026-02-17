---
name: brand-voice-codifier
description: Extend the Brand Kit with operational voice guidelines. Applies Nielsen Norman 4 Tone Dimensions, creates "This, Not That" framework, microcopy dictionary, and context-specific tone variations.
invocation: Use when Phase 1.4.5 begins, after direct response copy (1.4.4) is complete.
location: project
---

# Brand Voice Codifier

## Purpose

Transform the Brand Kit's personality archetype into actionable voice guidelines that ensure consistency across all touchpoints. This skill creates the "verbal interface" - operational rules that any writer (human or AI) can follow to maintain brand consistency.

## Prerequisites

Before running this skill, ensure:
- `docs/concept/master-concept.md` exists (personality hints, values)
- `docs/brand/brand-kit-guide.md` exists (brand personality archetype)
- `marketing/direct-response-copy.md` exists (from Phase 1.4.4 - provides copy examples to inform voice)

## Output

Extends: `docs/brand/brand-kit-guide.md` with new "Voice Codification" section

## Process

### Phase 1: Voice vs Tone Foundation

**Critical Distinction:**

- **Voice** = Consistent personality (the WHO)
  - Remains constant across all contexts
  - "If our brand were a person, they would be..."

- **Tone** = Contextual adaptation (the HOW)
  - Varies based on situation and user state
  - "In this situation, our brand would speak..."

### Phase 2: Apply Nielsen Norman 4 Tone Dimensions

Rate the brand on each dimension (1-5 scale):

#### Dimension 1: Funny ↔ Serious

| 1 (Serious) | 2 | 3 (Neutral) | 4 | 5 (Funny) |
|-------------|---|-------------|---|-----------|
| Critical infrastructure | Enterprise software | General B2B | Consumer tools | Entertainment |

**Questions to answer:**
- Are lives or significant money at stake? → Lean Serious
- Is the task creative or stress-relieving? → Lean Funny
- Does our audience appreciate wit? → Move toward Funny

#### Dimension 2: Formal ↔ Casual

| 1 (Formal) | 2 | 3 (Neutral) | 4 | 5 (Casual) |
|------------|---|-------------|---|------------|
| Legal, banking | Enterprise B2B | Professional services | Startups, SMB | Consumer apps |

**Questions to answer:**
- Do users expect "Dear" or "Hey"?
- Are contractions acceptable? (You're vs You are)
- Is first-person plural (we) or third-person used?

#### Dimension 3: Respectful ↔ Irreverent

| 1 (Respectful) | 2 | 3 (Neutral) | 4 | 5 (Irreverent) |
|----------------|---|-------------|---|----------------|
| Healthcare, legal | Traditional industries | Modern B2B | Disruptors | Counter-culture |

**Questions to answer:**
- Do we challenge the status quo or work within it?
- Is our audience comfortable with bold claims?
- Do we poke fun at competitors or industry conventions?

**Warning:** Irreverence should target the problem or status quo, NEVER the user.

#### Dimension 4: Enthusiastic ↔ Matter-of-Fact

| 1 (Matter-of-Fact) | 2 | 3 (Neutral) | 4 | 5 (Enthusiastic) |
|--------------------|---|-------------|---|------------------|
| Technical docs | Data/analytics | General SaaS | Marketing | Onboarding |

**Questions to answer:**
- Do we use exclamation points?
- Are superlatives appropriate? ("Amazing!", "Great job!")
- Is energy or precision more valued?

### Phase 3: Define Voice Coordinates

Create the brand's "Voice DNA":

```markdown
## Voice Coordinates

| Dimension | Score (1-5) | Description |
|-----------|-------------|-------------|
| Funny ↔ Serious | [X] | [One sentence explanation] |
| Formal ↔ Casual | [X] | [One sentence explanation] |
| Respectful ↔ Irreverent | [X] | [One sentence explanation] |
| Enthusiastic ↔ Matter-of-Fact | [X] | [One sentence explanation] |

**Voice Statement:**
We communicate with a [Adj 1] and [Adj 2] voice. We aim to make users feel [emotion].
```

### Phase 4: Create "This, Not That" Framework

Define the brand through contrast:

```markdown
## This, Not That

| We Are... | But We Are Not... | Why |
|-----------|-------------------|-----|
| **Confident** | Arrogant | We know our value, but never talk down to users |
| **Helpful** | Overbearing | We guide, we don't nag |
| **Clear** | Simplistic | We explain complex things simply, not dumb them down |
| **Friendly** | Unprofessional | Warm doesn't mean sloppy |
| **Expert** | Academic | We share knowledge without jargon |
| **Direct** | Blunt | We respect the user's time without being cold |
| [Add 2-3 more specific to this brand] | | |
```

### Phase 5: Build Vocabulary Guidelines

#### Preferred Terms
Words we use consistently:

| Instead of... | We say... | Reason |
|--------------|-----------|--------|
| Utilize | Use | Plain language |
| Leverage | Use, Apply | Less corporate |
| Solutions | Tools, Products | More specific |
| Synergy | Collaboration | Actually means something |
| Stakeholders | Team, People | More human |
| [Product-specific terms] | | |

#### Banned Words
Words we never use:

| Banned Word | Why | Alternative |
|-------------|-----|-------------|
| Best-in-class | Empty claim | Specific proof point |
| Cutting-edge | Overused | Describe the actual innovation |
| Seamless | Meaningless | Describe the actual integration |
| Robust | Vague | Describe the actual capability |
| Delve | AI-detected | Explore, Look into |
| Ensure | AI-detected | Make sure, Confirm |
| Utilize | Pretentious | Use |
| Leverage (as verb) | Corporate speak | Use, Apply |

### Phase 6: Tone Adaptation by Context

Define how voice adapts across touchpoints:

```markdown
## Tone by Context

### High-Stress Situations (Errors, Outages, Billing Issues)

**Tone Shift:**
- Humor: 1/5 (drop to serious)
- Formality: +1 (slightly more formal)
- Enthusiasm: 1/5 (matter-of-fact)
- Respect: 5/5 (maximum respect)

**Guidelines:**
- Lead with what happened, not apologies
- Provide clear next steps
- Never blame the user
- Avoid "Oops!" or "Whoops!"

**Example:**
- Bad: "Oops! Something went wrong. Try again!"
- Good: "We couldn't process your payment. Your card wasn't charged. [Try again] or [Contact support]"

### Success Moments (Completed Tasks, Milestones)

**Tone Shift:**
- Humor: +1 (slightly more playful)
- Enthusiasm: 5/5 (celebrate!)
- Keep formality consistent

**Guidelines:**
- Acknowledge the accomplishment
- Be specific about what was achieved
- Offer next step or related action

**Example:**
- Bad: "Done."
- Good: "Nice! Your first workflow is live. It'll run automatically at 9am tomorrow."

### Onboarding / First-Time Users

**Tone Shift:**
- Enthusiasm: 4-5/5 (welcoming energy)
- Formality: -1 (slightly warmer)

**Guidelines:**
- Reduce cognitive load
- One action per screen
- Celebrate small wins
- Don't overwhelm with features

### Documentation / Help Content

**Tone Shift:**
- Formality: Neutral
- Enthusiasm: 2/5 (clear, not hype)

**Guidelines:**
- Lead with the action
- Use numbered steps
- Include expected outcomes
- Keep personality minimal

### Marketing / Landing Pages

**Tone Shift:**
- Full brand personality
- Enthusiasm: Per brand coordinates

**Guidelines:**
- Lead with benefits
- Use social proof
- Clear CTAs
- More room for creativity
```

### Phase 7: Microcopy Dictionary

Standardize common UI text:

```markdown
## Microcopy Dictionary

### Buttons
| Action | Preferred Text | Avoid |
|--------|----------------|-------|
| Submit form | [Verb] + [Outcome]: "Send Message" | Submit, Click Here |
| Start trial | "Start Free Trial" or "Try [Product] Free" | Get Started |
| Learn more | "See How It Works" or "View Pricing" | Learn More |
| Cancel | "Cancel" (just the word) | Cancel Action |
| Delete | "Delete [Item]" (be specific) | Remove, Delete |
| Save | "Save Changes" or just "Save" | Submit |

### Empty States
| Context | Pattern |
|---------|---------|
| No data yet | [What this will show] + [How to add first item] |
| Search no results | [Acknowledge search] + [Suggestions] |
| Error loading | [What went wrong] + [What to do] |

### Confirmation Dialogs
| Type | Pattern |
|------|---------|
| Destructive action | [What will happen] + [Can it be undone?] |
| Success | [What happened] + [What's next] |

### Form Validation
| Type | Pattern |
|------|---------|
| Required field | "[Field] is required" (not "Please enter...") |
| Invalid format | "[Field] should be [format]. Example: [example]" |
| Success | Check icon, minimal text |

### Loading States
| Duration | Pattern |
|----------|---------|
| < 2 seconds | Spinner only |
| 2-5 seconds | "[Action]..." (e.g., "Saving...") |
| > 5 seconds | Progress indicator + "[Action]... This may take a moment." |
```

### Phase 8: Grammar & Mechanics

```markdown
## Grammar & Mechanics

### Capitalization
- **Headings:** [Sentence case / Title Case]
- **Buttons:** [Sentence case / Title Case]
- **Product features:** [lowercase unless proper noun]

### Punctuation
- **Headlines:** [No period / With period]
- **Button text:** No period
- **List items:** [Period if full sentence / No period if fragment]
- **Oxford comma:** [Yes / No]

### Numbers
- Spell out: [one through ten / one through nine]
- Use numerals: [11+ / 10+]
- Large numbers: 1,000 (with comma) or 1K (abbreviated)
- Percentages: 50% (numeral + symbol)
- Currency: $100 (symbol before)

### Contractions
- [Do use / Don't use] contractions
- Examples we use: you're, we're, it's, don't, can't
- Avoid: ain't, gonna, wanna

### Emoji Usage
- [Never / Sparingly / Freely]
- If used, only in: [marketing, social, success messages]
- Never in: [errors, legal, formal communications]
```

## Output Template

Add this section to `docs/brand/brand-kit-guide.md`:

```markdown
---

## Part 6: Voice Codification

*Operational guidelines for maintaining consistent brand voice across all touchpoints.*

### 6.1 Voice vs Tone

[Explanation of the distinction]

### 6.2 Voice Coordinates

[4-dimension ratings with explanations]

### 6.3 Voice Statement

[One-paragraph summary of brand voice]

### 6.4 This, Not That

[Contrast table]

### 6.5 Vocabulary Guidelines

#### Preferred Terms
[Table]

#### Banned Words
[Table]

### 6.6 Tone by Context

[Context-specific guidelines]

### 6.7 Microcopy Dictionary

[Standardized UI text]

### 6.8 Grammar & Mechanics

[Style rules]

---

*Voice Codification generated by brand-voice-codifier skill*
*Last updated: [Date]*
```

## Quality Checklist

Before completing, verify:
- [ ] Read Master Concept for personality cues
- [ ] Read existing Brand Kit thoroughly
- [ ] Rated all 4 tone dimensions with rationale
- [ ] Created "This, Not That" with 6+ contrasts
- [ ] Defined preferred and banned vocabulary
- [ ] Created tone guidelines for 4+ contexts
- [ ] Built microcopy dictionary for common UI patterns
- [ ] Documented grammar/mechanics decisions
- [ ] Integrated seamlessly into existing Brand Kit structure
