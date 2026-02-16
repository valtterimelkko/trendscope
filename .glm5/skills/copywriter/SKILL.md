# Copywriter Skill

**Purpose:** Generate context-aware, conversion-optimized content for all template content slots, applying SaaS copywriting best practices while maintaining brand voice consistency and marketing alignment.

**Model:** Haiku (via content-copywriter agent)

---

## Overview

This skill generates professional SaaS copy for all content slots in a selected template. It operates at the intersection of:
1. **Marketing Strategy** - Uses positioning, hooks, keywords, and lead magnets from marketing docs
2. **Brand Identity** - Applies voice/tone from Brand Kit
3. **UX Design** - Respects user flows and emotional journey from UX Design docs
4. **Copywriting Best Practice** - Applies research-backed frameworks for conversion

---

## Context Awareness Matrix

The copywriter skill MUST check for and incorporate these sources in priority order:

### 1. Marketing Folder (REQUIRED - from Phase 1.4)
Location: `marketing/`

| Source File | What to Extract | How to Apply |
|-------------|-----------------|--------------|
| `positioning-angles.md` | Unique value propositions, differentiation hooks | Use as foundation for all headlines and CTAs |
| `keyword-research.md` | Target keywords, semantic clusters | Incorporate naturally into headlines, meta, body copy |
| `lead-magnet.md` | Opt-in hooks, value promises | Inform CTA copy and conversion messaging |
| `direct-response-copy.md` | Hooks, persuasion frameworks, angles | Use for hero headlines, feature benefits |
| `seo-content.md` | SEO guidelines, content structure | Apply to landing page copy structure |

**These files are REQUIRED inputs from Phase 1.4.** Extract hooks, positioning, keywords and USE THEM VERBATIM where possible.

### 2. Brand Kit (Required)
Location: `docs/brand/brand-kit-guide.md`

| Element | What to Extract | How to Apply |
|---------|-----------------|--------------|
| Voice descriptors | Personality traits (professional, playful, etc.) | Tone calibration for all copy |
| Tone guidelines | Formality level, humor tolerance | Context-appropriate modulation |
| Key phrases | "We say X, not Y" rules | Direct vocabulary substitution |
| Industry | SaaS category context | Category-specific patterns |
| Target audience | User persona details | Audience qualification in copy |
| **Voice Codification section** | 4 Tone Dimensions, "This, Not That" framework | Detailed voice rules from Phase 1.4.5 |

### 3. Master Concept (Required)
Location: `docs/concept/master-concept.md`

| Element | What to Extract | How to Apply |
|---------|-----------------|--------------|
| Value proposition | Core benefit promise | Hero headline foundation |
| Key features | Feature list with descriptions | FAB framework for feature sections |
| Target market | Who the product serves | Audience callouts |
| Problem statement | Pain points solved | Risk reversal copy |
| Unique mechanism | How it works | Subheadline content |

### 4. UX Design (Required)
Location: `docs/mvp-ux-[project].md`

| Element | What to Extract | How to Apply |
|---------|-----------------|--------------|
| User journey stages | Emotional states at each step | Tone modulation |
| Key interactions | Critical user moments | Success/error message context |
| Onboarding flow | Step sequence | Progress copy and guidance |
| Empty states | When user sees blank screens | Educational/encouraging copy |
| Error scenarios | What can go wrong | No-blame error messages |

---

## Slot Type Frameworks

Apply the appropriate framework based on slot type from `slots.json`:

### Headlines (`type: "headline"`)
**Framework:** Value + Mechanism (from research)

**Formula:** `[Adjective] [Noun] that [Action] without [Pain Point]`

**Pattern Selection:**
| Pattern | When to Use | Example |
|---------|-------------|---------|
| Risk Reversal | Competitive markets | "Automate payroll without spreadsheets" |
| Identity Callout | Niche/vertical SaaS | "The [category] for [specific audience]" |
| Direct Outcome | Utility tools | "[Verb] [outcome] in [timeframe]" |
| Market Leader | Established position | "The #1 [category]" |

**Anti-Patterns to AVOID:**
- Vague aspirational: "Reimagine the future of..."
- Generic: "Empower your enterprise"
- Feature-first: "AI-powered platform that..."

**Marketing Integration:**
- CHECK `marketing/direct-response-copy.md` for pre-approved hooks
- USE positioning angles from `marketing/positioning-angles.md`
- INCORPORATE target keywords from `marketing/keyword-research.md`

### Body Text (`type: "body"`)
**Framework:** Feature-Advantage-Benefit (FAB)

**Structure:**
1. Feature (What) - Technical capability
2. Advantage (How) - Functional benefit
3. Benefit (Why) - Emotional/financial payoff

**Guidelines:**
- Lead with benefit, support with feature
- Use specific numbers over vague claims ("saves 20 hours/week" not "saves time")
- Match formality to context (marketing = confident, error = apologetic)

### Buttons/CTAs (`type: "button"`)
**Framework:** "I Want To" Test

**Formula:** Button text should complete "I want to..."

**Examples:**
| ❌ Fail | ✅ Pass |
|---------|---------|
| Submit | Get My Report |
| Register | Start Building |
| Login | Access Dashboard |
| Buy | Start Free Trial |

**Click Triggers (add below button):**
- "No credit card required"
- "Cancel anytime"
- "Free for 14 days"
- "Join 10,000+ teams"

### Section Titles (`type: "section_title"`)
**Framework:** Benefit + Curiosity

**Patterns:**
- "Everything you need, nothing you don't"
- "Simple, transparent [topic]"
- "[Outcome] without [common pain]"

### Feature Cards (`type: "feature_title"` + description)
**Framework:** FAB Condensed

**Title:** 2-4 words, benefit-focused
**Description:** 1-2 sentences explaining mechanism

**Category-Specific Patterns:**

| SaaS Category | Copy Lean | Example |
|---------------|-----------|---------|
| Analytics/Dashboard | Features + Data | "Real-time metrics, privacy-first" |
| Productivity/Tasks | Benefits + Speed | "Get clarity on who's doing what" |
| Content/Creator | Empowerment + Growth | "Turn your audience into income" |

### Error Messages (`type: "error"`)
**Framework:** 4-H (Human, Helpful, Humble, Humorous-with-caution)

**Structure:**
1. Acknowledge (what happened)
2. Explain (why, briefly)
3. Guide (how to fix)

**Examples:**
| Context | ❌ Technical | ✅ Refactored |
|---------|-------------|---------------|
| Login fail | "Auth Failed: Bad Creds" | "That email or password didn't match. Please try again." |
| Form error | "Field Required" | "Please enter your name so we know what to call you." |
| System error | "503 Service Unavailable" | "We're doing maintenance. Back by 2:00 PM EST." |

**Rules:**
- NEVER blame the user
- ALWAYS provide next step
- NO error codes in user-facing text
- Serious errors = serious tone (no jokes for payment failures)

### Empty States (`type: "empty_state"`)
**Framework:** Guidance + Education

**Components:**
1. State description: "No [items] yet"
2. Value education: "Tasks help you track work and collaborate"
3. Primary action: "Create your first [item]"

**Positive Framing:**
- Turn completion into reward: "All caught up! Enjoy your day."
- Focus on potential: "Ready to add your first project?"

### Success Messages (`type: "success"` or confirmation toasts)
**Framework:** Confirmation + Reinforcement

**Patterns:**
- Functional: "Settings saved."
- Reassuring: "You're all set! Your campaign is live."
- Delightful: "Done! Task completed." (match brand playfulness)

---

## Voice Modulation by Context

The same brand voice must adapt tone based on user emotional state:

| Context | User Emotion | Tone | Example |
|---------|--------------|------|---------|
| Marketing/Landing | Curious, skeptical | Confident, promising | "Ship faster with [Product]" |
| Onboarding | Hopeful, confused | Warm, guiding | "Let's set up your first project" |
| Success | Satisfied | Celebratory | "You're all set!" |
| Error | Frustrated, anxious | Calm, apologetic, direct | "We couldn't save changes. Retrying..." |
| Billing | Serious, defensive | Professional, clear | "Invoice #1024 is due tomorrow" |
| Danger Zone | Careful, scared | Serious, explicit | "This action cannot be undone" |

---

## SEO Integration

When `marketing/keyword-research.md` exists:

1. **Primary Keyword:** Include in hero headline if natural
2. **Secondary Keywords:** Distribute across feature titles and body
3. **Semantic Clusters:** Use related terms throughout
4. **Meta Considerations:** Optimize for 60-char title, 160-char description limits

**Natural Integration Rules:**
- Keywords must read naturally - never keyword stuff
- One primary keyword per major section maximum
- User experience > SEO when in conflict

---

## Process Steps

### Step 1: Load Context Sources
```
READ: marketing/ folder (if exists)
  - positioning-angles.md → positioning_angles
  - keyword-research.md → keywords
  - direct-response-copy.md → hooks
  - lead-magnet.md → lead_magnet_hooks
  - seo-content.md → seo_guidelines

READ: docs/brand/brand-kit-guide.md → brand_kit (includes Voice Codification section if exists)
READ: docs/concept/master-concept.md → master_concept
READ: docs/ux/ux-design.md → ux_design (if exists)
READ: templates/{selected}/content/slots.json → slots
```

### Step 2: Build Voice Profile
```
voice_profile = {
  personality: brand_kit.voice OR voice_override,
  formality: brand_kit.tone_formality,
  industry: brand_kit.industry OR master_concept.category,
  audience: master_concept.target_market,
  positioning: positioning_angles.primary_angle (if exists)
}
```

### Step 3: Process Each Slot
```
FOR each slot in slots:
  1. Identify slot type (headline, body, button, error, etc.)
  2. Select appropriate framework
  3. Check for marketing-provided content (hooks, keywords)
  4. Generate copy applying:
     - Framework rules
     - Voice profile
     - maxLength constraint
     - Marketing keywords (if applicable)
  5. Validate:
     - Length within limit
     - Voice consistency
     - No anti-patterns
     - SEO keyword presence (for landing page slots)
```

### Step 4: Consistency Check
```
VERIFY:
- Same value proposition language across all sections
- Consistent terminology (don't switch between "users" and "customers")
- Progressive disclosure (simple → detailed as user goes deeper)
- Emotional arc matches user journey
```

### Step 5: Output Generated Content
```
OUTPUT: Generated content mapped to slot IDs
FORMAT: JSON matching slots.json structure with generated values

EXAMPLE OUTPUT:
{
  "landing.hero.headline": "Simple analytics for privacy-conscious teams",
  "landing.hero.subheadline": "Get the insights you need without...",
  "landing.cta.primary": "Start Free Trial",
  ...
}
```

---

## Validation Checklist

Before finalizing generated content:

- [ ] All slots have content within maxLength
- [ ] Hero headline uses Value+Mechanism framework
- [ ] CTAs pass "I Want To" test
- [ ] Error messages follow 4-H framework
- [ ] Marketing keywords included (if marketing docs exist)
- [ ] Voice consistent across all slots
- [ ] No vague/lazy copy anti-patterns
- [ ] Empty states are educational and encouraging
- [ ] Billing/danger copy is appropriately serious
- [ ] Feature copy uses FAB framework

---

## Helper Script

**Script:** `.claude/scripts/templates/generate-content.py`

**Usage:**
```bash
# Validate slots structure
python3 generate-content.py --slots templates/analytics-dashboard/content/slots.json --validate

# List all slots
python3 generate-content.py --slots templates/analytics-dashboard/content/slots.json --list
```

---

## Category-Specific Guidelines

### Analytics Dashboard Template
- **Persona:** Data-driven, seeks truth
- **Copy lean:** Precision + Features
- **Key pattern:** Clarity over persuasion
- **Empty state:** "Waiting for data. Add this script to start tracking."

### Productivity Tool Template
- **Persona:** Busy, overwhelmed, seeks order
- **Copy lean:** Benefits + Speed
- **Key pattern:** "Get clarity on..." language
- **Empty state:** "Ready to organize? Create your first project."

### Content Creator Template
- **Persona:** Creative, ambitious, seeks growth
- **Copy lean:** Empowerment + Outcomes
- **Key pattern:** Monetization and audience focus
- **Empty state:** "Your audience is waiting. Create your first post."

---

## Escalation Triggers

Escalate to Co-CEO if:
- Marketing positioning conflicts with brand kit voice
- No clear value proposition found in source documents
- Slot type not recognized in framework
- 3 consecutive generation attempts fail validation

---

## References

Based on research synthesized from:
- Copy Hackers: Landing page frameworks
- Nielsen Norman Group: Error message UX
- Stripe Atlas: Technical audience copy
- Slack/Linear/Notion: Voice consistency patterns
- UX Writing Hub: Empty state patterns
- Userpilot: SaaS onboarding copy

Full research: `docs/saas-copywriting-research.md`
