---
name: template-personalizer
description: Use when applying brand identity (colors, typography, logo) to a selected frontend template. Reads the Brand Kit and updates CSS tokens, Tailwind config, and brand assets in the template.
---

# Template Personalizer

## Overview

Apply brand identity from the Brand Kit to the selected frontend template. This transforms a generic template into a branded product by updating CSS custom properties, Tailwind configuration, and integrating brand assets.

**Core principle:** Brand tokens are the bridge between design decisions and code. Update tokens systematically, and the entire template reflects the brand.

## When to Use

- After template selection is confirmed (Phase 4.3.1)
- When Brand Kit exists with defined colors and typography
- Before content generation (copywriter needs styled template)

## Pre-Requisites

**Required inputs:**
```bash
# Verify Brand Kit exists
ls docs/brand/brand-kit-guide.md

# Verify template is selected (path will be provided)
ls templates/{selected-template}/frontend/styles/tokens.css
ls templates/{selected-template}/frontend/tailwind.config.js
```

## Process Workflow

### Phase 1: Extract Brand Values

Read `docs/brand/brand-kit-guide.md` and extract:

#### Colors
| Token Category | Brand Kit Section | Example |
|----------------|-------------------|---------|
| Primary | Primary Brand Color | #2563EB |
| Secondary | Secondary/Accent | #7C3AED |
| Accent | Accent/Highlight | #F97316 |
| Background | Background colors | #FFFFFF, #F8FAFC |
| Foreground | Text colors | #0F172A, #64748B |
| Success | Semantic - Success | #10B981 |
| Warning | Semantic - Warning | #F59E0B |
| Error | Semantic - Error | #EF4444 |
| Info | Semantic - Info | #3B82F6 |

#### Typography
| Token | Brand Kit Section | Example |
|-------|-------------------|---------|
| Font Display | Heading typeface | "Inter", sans-serif |
| Font Body | Body typeface | "Inter", sans-serif |
| Font Mono | Code typeface | "JetBrains Mono", monospace |

### Phase 2: Update CSS Tokens

Location: `templates/{template}/frontend/styles/tokens.css`

**Token structure:**
```css
:root {
  /* Brand Colors */
  --color-primary: #2563EB;
  --color-primary-hover: #1D4ED8;
  --color-primary-light: #DBEAFE;
  
  --color-secondary: #7C3AED;
  --color-secondary-hover: #6D28D9;
  
  --color-accent: #F97316;
  --color-accent-hover: #EA580C;
  
  /* Backgrounds */
  --color-background: #FFFFFF;
  --color-background-secondary: #F8FAFC;
  --color-background-tertiary: #F1F5F9;
  
  /* Foregrounds */
  --color-foreground: #0F172A;
  --color-foreground-secondary: #475569;
  --color-foreground-muted: #94A3B8;
  
  /* Semantic Colors */
  --color-success: #10B981;
  --color-success-light: #D1FAE5;
  --color-warning: #F59E0B;
  --color-warning-light: #FEF3C7;
  --color-error: #EF4444;
  --color-error-light: #FEE2E2;
  --color-info: #3B82F6;
  --color-info-light: #DBEAFE;
  
  /* Typography */
  --font-display: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-body: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
  
  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-full: 9999px;
}

/* Dark Mode Overrides */
[data-theme="dark"] {
  --color-background: #0F172A;
  --color-background-secondary: #1E293B;
  --color-background-tertiary: #334155;
  
  --color-foreground: #F8FAFC;
  --color-foreground-secondary: #CBD5E1;
  --color-foreground-muted: #64748B;
}
```

**Update process:**
1. Read current tokens.css
2. Replace color values with Brand Kit colors
3. Replace font families with Brand Kit typography
4. Generate hover/light variants automatically (see Color Utilities below)
5. Preserve structure and comments

### Phase 3: Update Tailwind Config

Location: `templates/{template}/frontend/tailwind.config.js`

**Sync Tailwind with CSS tokens:**
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'var(--color-primary)',
          hover: 'var(--color-primary-hover)',
          light: 'var(--color-primary-light)',
        },
        secondary: {
          DEFAULT: 'var(--color-secondary)',
          hover: 'var(--color-secondary-hover)',
        },
        accent: {
          DEFAULT: 'var(--color-accent)',
          hover: 'var(--color-accent-hover)',
        },
        // ... other colors reference CSS variables
      },
      fontFamily: {
        display: 'var(--font-display)',
        body: 'var(--font-body)',
        mono: 'var(--font-mono)',
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        full: 'var(--radius-full)',
      },
    },
  },
};
```

### Phase 4: Validate Accessibility

**Contrast requirements (WCAG AA):**
| Combination | Minimum Ratio | Check |
|-------------|---------------|-------|
| Foreground on Background | 4.5:1 | Text readability |
| Primary on Background | 4.5:1 | Button text |
| Foreground on Primary | 4.5:1 | Inverse buttons |

**Validation script:**
```bash
python3 .shared/scripts/templates/check-brand-tokens.py templates/{template}
```

**If contrast fails:**
1. Adjust the lighter/darker variant, not the primary color
2. For buttons with white text on primary: ensure primary is dark enough
3. Document any accessibility trade-offs

### Phase 5: Generate Color Variants

**Automatic variant generation:**

For each primary color, generate:
- **Hover:** 10% darker (reduce lightness in HSL)
- **Light:** 90% lighter (high lightness, low saturation)
- **Dark:** 20% darker (for dark mode accents)

**Helper function (conceptual):**
```python
def generate_variants(hex_color):
    # Convert to HSL
    h, s, l = hex_to_hsl(hex_color)
    
    return {
        'default': hex_color,
        'hover': hsl_to_hex(h, s, max(0, l - 10)),
        'light': hsl_to_hex(h, max(10, s - 40), min(95, l + 40)),
        'dark': hsl_to_hex(h, s, max(0, l - 20)),
    }
```

### Phase 6: Update Brand Assets

**Logo integration:**
1. Copy logo files to `templates/{template}/frontend/public/`
   - `logo.svg` (primary)
   - `logo-dark.svg` (for dark backgrounds)
   - `favicon.ico`
   - `apple-touch-icon.png`

2. Update references in:
   - `app/layout.tsx` (favicon, apple-touch-icon)
   - Header/navigation components (logo)
   - Footer component (logo)

**If logo files don't exist:**
- Document that logos need to be created
- Use placeholder or text-based logo
- Note in output report

## Output Checklist

After completion, verify:

- [ ] `tokens.css` updated with all brand colors
- [ ] `tokens.css` includes dark mode overrides
- [ ] `tailwind.config.js` references CSS variables
- [ ] Typography tokens match Brand Kit fonts
- [ ] Contrast validation passes (or issues documented)
- [ ] Logo files copied (or noted as missing)
- [ ] Component references updated for logos

## Helper Script

Location: `.shared/scripts/templates/apply-brand-tokens.py`

**Usage:**
```bash
python3 .shared/scripts/templates/apply-brand-tokens.py \
  --template templates/analytics-dashboard \
  --brand-kit docs/brand/brand-kit-guide.md \
  --validate
```

**Script capabilities:**
1. Parse Brand Kit for color/typography values
2. Update tokens.css with extracted values
3. Generate hover/light variants
4. Validate contrast ratios
5. Report any issues found

## Common Issues & Solutions

### Issue: Brand Kit uses color names, not hex

**Solution:** Map common names to hex:
```
"Blue" → #2563EB
"Purple" → #7C3AED
"Green" → #10B981
```

Or ask Co-CEO to clarify specific hex values.

### Issue: Only primary color provided

**Solution:** Generate complementary palette:
- Secondary: Analogous or complementary hue
- Accent: High-contrast highlight color
- Use color theory principles

### Issue: Font not available as web font

**Solution:**
1. Check Google Fonts availability
2. Add to `app/layout.tsx` font imports
3. Fallback to similar system font if unavailable

### Issue: Dark mode colors not specified

**Solution:** Auto-generate dark mode:
- Invert background (light → dark)
- Adjust foreground (dark → light)
- Keep semantic colors, adjust lightness slightly

## Verification

After applying tokens, visually verify:

1. **Landing page:** Hero section, CTAs, feature cards
2. **Auth pages:** Login/signup forms, buttons
3. **Dashboard:** Charts, cards, navigation
4. **Settings:** Forms, toggles, danger zones

Run the template locally:
```bash
cd templates/{template}/frontend
npm install
npm run dev
```

Check in browser for visual consistency.

## Error Handling

If Brand Kit is incomplete:
1. Document missing values
2. Use sensible defaults from template
3. Report gaps to Co-CEO for user clarification

If tokens.css structure differs from expected:
1. Adapt to existing structure
2. Add missing tokens without removing existing ones
3. Document structural changes made

## Output Report

Provide summary to Co-CEO:

```markdown
## Brand Personalization Complete

**Template:** {template-name}
**Brand Kit:** docs/brand/brand-kit-guide.md

### Applied Changes

| File | Changes |
|------|---------|
| tokens.css | Updated 24 color tokens, 3 font tokens |
| tailwind.config.js | Synced with CSS variables |
| public/ | Copied logo.svg, favicon.ico |

### Accessibility Check

| Check | Status |
|-------|--------|
| Text contrast | ✓ Pass (5.2:1) |
| Button contrast | ✓ Pass (4.8:1) |
| Link visibility | ✓ Pass |

### Notes
- [Any issues or manual steps needed]
```
