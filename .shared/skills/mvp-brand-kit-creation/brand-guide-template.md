# Brand Kit & Guide Template

Use this template structure when creating the brand guide document for an MVP project.

## Brand Guide Document Template

Copy and customize the following structure:

```markdown
# [Service Name] Brand Guide

## 1. Brand Heart

### Mission
[One sentence: Why does this product exist?]

### Vision
[One sentence: What future state does this product enable?]

### Value Proposition
[For [target user], [product name] is a [category] that [key benefit]. Unlike [competitor/alternative], we [unique differentiator].]

### Brand Personality
- Attribute 1: [e.g., "Confident but not arrogant"]
- Attribute 2: [e.g., "Helpful but not patronizing"]
- Attribute 3: [e.g., "Professional but not corporate"]

---

## 2. Logo System

### Primary Lockup
**File:** `assets/logo-primary.svg`

**Usage:** Website header, documents, presentations
**Clear space:** Minimum [X]px on all sides
**Minimum size:** [X]px width

### Symbol/Icon
**File:** `assets/logo-icon.svg`

**Usage:** Favicon, app icons, social avatars
**Minimum size:** 16x16px

### Logo Don'ts
- Do not stretch or distort
- Do not change colors outside approved palette
- Do not add effects (shadows, gradients, outlines)
- Do not place on busy backgrounds without contrast

---

## 3. Color Palette

### Primary Colors

| Name | HEX | RGB | Usage |
|------|-----|-----|-------|
| Primary | #[XXXXXX] | rgb(X,X,X) | CTAs, key navigation |
| Primary Light | #[XXXXXX] | rgb(X,X,X) | Hover states, backgrounds |
| Primary Dark | #[XXXXXX] | rgb(X,X,X) | Active states, text |

### Semantic Colors (Fixed)

| Name | HEX | Usage |
|------|-----|-------|
| Success | #28A745 | Confirmations, positive feedback |
| Warning | #FFC107 | Cautions, important notices |
| Error | #DC3545 | Errors, destructive actions |
| Info | #17A2B8 | Informational messages |

### Neutrals

| Name | HEX | Usage |
|------|-----|-------|
| Text Primary | #[XXXXXX] | Main body text |
| Text Secondary | #[XXXXXX] | Secondary text, labels |
| Border | #[XXXXXX] | Dividers, input borders |
| Background | #[XXXXXX] | Page background |
| Surface | #[XXXXXX] | Cards, modals |

---

## 4. Typography

### Font Stack
**Primary:** [Font Name], [Fallback], sans-serif
**Monospace:** [Font Name], monospace (for code)

### Type Scale

| Style | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| H1 | 32px | 700 | 1.2 | Page titles |
| H2 | 24px | 600 | 1.3 | Section headers |
| H3 | 20px | 600 | 1.4 | Subsections |
| Body | 16px | 400 | 1.5 | Main content |
| Small | 14px | 400 | 1.5 | Captions, metadata |
| Caption | 12px | 400 | 1.4 | Labels, hints |

---

## 5. Voice & Tone

### Brand Voice (Constant)
Our voice is [Personality Adjective 1], [Personality Adjective 2], and [Personality Adjective 3].

**We are:**
- [Positive trait] but not [negative extreme]
- [Positive trait] but not [negative extreme]
- [Positive trait] but not [negative extreme]

### Tone Adaptation

| Context | Tone | Example |
|---------|------|---------|
| Success | Enthusiastic, celebratory | "Your project is live!" |
| Error | Calm, helpful, apologetic | "Something went wrong. Here's how to fix it." |
| Onboarding | Welcoming, encouraging | "Welcome! Let's get you set up." |
| Destructive action | Serious, clear | "This will permanently delete your data." |

### Microcopy Dictionary

| Term | We Use | We Don't Use |
|------|--------|--------------|
| Authentication | Log in | Sign in, Login, Log-in |
| Deletion | Delete | Remove, Trash, Erase |
| User | Member | User, Customer, Client |
| Confirmation | Got it | OK, Okay, Yes |
| Cancellation | Cancel | Never mind, Go back |

---

## 6. Iconography

### Icon Library
Using: [Library Name] (e.g., Phosphor Icons, Heroicons)

### Style Guidelines
- Stroke width: [X]px
- Corner radius: [X]px
- Style: [Outline/Filled] (use filled for active states)

### Common Icons

| Action | Icon | Notes |
|--------|------|-------|
| Close | × | Top-right of modals |
| Menu | ≡ | Mobile navigation |
| Settings | ⚙ | Account/preferences |
| User | ○ | Profile, account |

---

## 7. Asset Locations

All brand assets stored at:
```
docs/brand/
├── assets/
│   ├── logo-primary.svg
│   ├── logo-icon.svg
│   ├── logo-wordmark.svg
│   └── favicon.ico
├── brand-kit-guide.md (this file)
├── color-palette.md
└── microcopy-dictionary.md
```

---

## 8. Quick Reference

### Color CSS Variables
```css
:root {
  --color-primary: #[XXXXXX];
  --color-primary-light: #[XXXXXX];
  --color-primary-dark: #[XXXXXX];
  --color-success: #28A745;
  --color-warning: #FFC107;
  --color-error: #DC3545;
  --color-info: #17A2B8;
  --color-text-primary: #[XXXXXX];
  --color-text-secondary: #[XXXXXX];
  --color-border: #[XXXXXX];
  --color-background: #[XXXXXX];
  --color-surface: #[XXXXXX];
}
```

### Typography CSS Variables
```css
:root {
  --font-family: '[Font Name]', [fallback], sans-serif;
  --font-mono: '[Mono Font]', monospace;
  --font-size-h1: 32px;
  --font-size-h2: 24px;
  --font-size-h3: 20px;
  --font-size-body: 16px;
  --font-size-small: 14px;
  --font-size-caption: 12px;
}
```

### Spacing CSS Variables
```css
:root {
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;
  --spacing-3xl: 64px;
}
```
```

## Design Token Export Format

For design-to-code handoff, export tokens in this JSON structure:

```json
{
  "color": {
    "primary": { "value": "#XXXXXX" },
    "primary-light": { "value": "#XXXXXX" },
    "primary-dark": { "value": "#XXXXXX" },
    "success": { "value": "#28A745" },
    "warning": { "value": "#FFC107" },
    "error": { "value": "#DC3545" },
    "info": { "value": "#17A2B8" }
  },
  "typography": {
    "font-family": { "value": "'[Font Name]', sans-serif" },
    "font-size-h1": { "value": "32px" },
    "font-size-body": { "value": "16px" }
  },
  "spacing": {
    "xs": { "value": "4px" },
    "sm": { "value": "8px" },
    "md": { "value": "16px" },
    "lg": { "value": "24px" },
    "xl": { "value": "32px" }
  }
}
```

## B2B vs B2C Considerations

### B2B SaaS
- Use industry-specific terminology (signals domain expertise)
- Formal but not stiff voice
- Emphasize trust and reliability in messaging
- Professional color palette (blues, greys, greens)

### B2C Apps
- Casual, colloquial language acceptable
- More expressive, personality-forward voice
- Can use bolder, more saturated colors
- Emoji usage may be appropriate

## Accessibility Validation

Before finalizing, verify:

| Check | Tool | Requirement |
|-------|------|-------------|
| Text contrast | WebAIM Contrast Checker | 4.5:1 minimum |
| UI component contrast | Stark, Coolors | 3:1 minimum |
| Color blindness | Coolors Color Blindness Simulator | Distinguishable variants |
| Font readability | Manual review | Clear at 14px |
