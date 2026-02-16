---
name: consistency-quality-check
description: Ensures standardized, comprehensive quality checks across all created documents and architecture files. Without a skill, quality checking would be inconsistent and the Co-CEO would need to pass verbose instructions each time.
---

# Consistency & Quality Check

## Overview

Validate completeness and cross-document consistency for all MVP development artifacts. Identifies blockers, warnings, and suggestions with clear severity levels.

**Core principle:** Quality gates prevent cascading errors. A typo in the Master Concept becomes a bug in the code.

## When to Use

- After Phase 1 & 2 completion (Quality Gate #1)
- After stage architecture files are created (Quality Gate #2)
- Before proceeding to next major phase
- When resuming a project to assess current state

## The Process

### Step 1: Identify Documents to Validate

**Phase 1.1-1.3 Core Documents:**
```bash
# Check which documents exist
ls -la docs/concept/ docs/brand/ docs/*.md
```

Expected files:
- `docs/concept/master-concept.md`
- `docs/brand/brand-kit-guide.md` (including Voice Codification section from Phase 1.4.5)

**Phase 1.4 Marketing Foundation:**
```bash
# Check marketing documents
ls -la marketing/
```

Expected files:
- `marketing/positioning-angles.md`
- `marketing/keyword-research.md`
- `marketing/lead-magnet.md`
- `marketing/direct-response-copy.md`
- `marketing/seo-content.md`

**Phase 2.1-2.2 Design Documents:**
- `docs/mvp-ux-*.md`
- `docs/Project-Technical-Architecture.md`

**Phase 4+ Documents:**
- `docs/stages/stage-*.md`

### Step 2: Run Individual Document Validators

**Master Concept:**
```bash
.shared/scripts/master-concept/validate-concept.sh docs/concept/master-concept.md
```

**All Documents (structure check):**
```bash
.shared/scripts/consistency-check/validate-document-structure.sh docs/
.shared/scripts/consistency-check/validate-document-structure.sh marketing/
```

### Step 3: Cross-Reference Check

Run cross-document consistency validation:
```bash
.shared/scripts/consistency-check/cross-reference-check.sh docs/
```

**What it checks:**
- Service name matches across all documents
- Brand colors in Brand Kit match those in UX document
- Features in Master Concept scope appear in UX flows
- UX flows map to Technical PRD features
- API endpoints in PRD match stage architecture files

### Step 4: API Contract Validation (if code exists)

After implementation begins:
```bash
python3 .shared/scripts/api-validation/validate-api-contracts.py --prd docs/Project-Technical-Architecture.md --frontend src/
```

### Step 5: Categorize Issues

| Severity | Criteria | Action |
|----------|----------|--------|
| BLOCKER | Breaks functionality, conflicts that prevent progress | Must fix before proceeding |
| WARNING | Should fix, inconsistency that causes confusion | Fix before implementation, can proceed with acknowledgment |
| SUGGESTION | Nice-to-have improvements | Optional, document for later |

### Step 6: Generate Report

Output format:
```markdown
# Quality Check Report

**Date:** [Date]
**Documents Checked:** [List]
**Overall Status:** ✅ PASS | ⚠️ WARNINGS | ❌ BLOCKERS

## Blockers (Must Fix)

### [Issue 1]
- **Location:** [File, section]
- **Issue:** [Description]
- **Impact:** [What breaks if not fixed]
- **Suggested Fix:** [How to fix]

## Warnings (Should Fix)

### [Issue 1]
- **Location:** [File, section]
- **Issue:** [Description]
- **Suggested Fix:** [How to fix]

## Suggestions (Optional)

- [Suggestion 1]
- [Suggestion 2]

## Auto-Fixed Issues

- [What was auto-fixed, where]
```

## Validation Checklists

### Master Concept Checklist

- [ ] Executive Summary present and <100 words
- [ ] Problem Statement clearly defines the pain
- [ ] Target Audience with behavioral description
- [ ] Jobs to Be Done articulated
- [ ] Solution Vision without technical details
- [ ] MoSCoW scope with explicit "Won't Have"
- [ ] Success metrics are quantifiable
- [ ] Risks and critical assumptions listed
- [ ] Service name appears consistently

### Brand Kit Checklist

- [ ] Logo system with variants documented
- [ ] Primary brand color defined (HEX)
- [ ] Semantic colors defined (success/warning/error/info)
- [ ] Typography decisions made
- [ ] Voice & tone attributes (3-4 key traits)
- [ ] Microcopy dictionary started
- [ ] Service name matches Master Concept

### UX Design Checklist

- [ ] User flows for all critical journeys
- [ ] Decision points and error paths documented
- [ ] 4 states for major screens (ideal, empty, loading, error)
- [ ] Accessibility requirements noted
- [ ] Features align with Master Concept scope
- [ ] Brand colors referenced from Brand Kit
- [ ] Messaging aligns with marketing positioning (if Phase 1.4 complete)

### Marketing Foundation Checklist (Phase 1.4)

**Positioning Angles:**
- [ ] Primary positioning angle selected
- [ ] 3+ alternative angles documented
- [ ] Target persona alignment verified
- [ ] Headline variants present

**Keyword Research:**
- [ ] 6 Circles Method applied
- [ ] Keywords mapped to funnel stages (ToFu/MoFu/BoFu)
- [ ] Priority scoring completed
- [ ] Top priority keywords identified

**Lead Magnet:**
- [ ] Persona analysis present
- [ ] 2-3 lead magnet formats selected
- [ ] Each format has detailed specs
- [ ] Nurture sequence outlined

**Direct Response Copy:**
- [ ] Landing page copy blocks present (Hero, Problem, Solution, Features, FAQ, CTA)
- [ ] Copy matches brand voice from Brand Kit
- [ ] Email sequence outlined
- [ ] A/B test variants included

**Brand Voice Codification (in brand-kit-guide.md):**
- [ ] Voice vs Tone distinction documented
- [ ] 4 Tone Dimensions rated (1-5 each)
- [ ] "This, Not That" framework with 10+ examples
- [ ] Context-specific variations defined
- [ ] Microcopy patterns present

**SEO Content:**
- [ ] 3-5 pillar topics identified
- [ ] Cluster structure for each pillar
- [ ] Content mapped to funnel stages
- [ ] 6-month calendar present

### Technical PRD Checklist

- [ ] All 9 sections present
- [ ] Critical User Journeys defined
- [ ] Database schema with RLS policies
- [ ] API contracts with endpoints, payloads, errors
- [ ] Implementation stages defined
- [ ] Git workflow for AI agents
- [ ] "DO NOT" constraints present
- [ ] Features trace back to UX flows

### Stage Architecture Checklist

- [ ] Uses stage-architecture-template structure
- [ ] Dependencies correctly identified
- [ ] API endpoints consistent with other stages
- [ ] Database changes don't conflict
- [ ] Testing requirements defined
- [ ] Critical constraints present
- [ ] Empty Progress Log and Issues sections ready

## Cross-Document Consistency Rules

### Service Name Consistency
The service name must be identical in:
- Master Concept (title, Executive Summary)
- Brand Kit (Logo system)
- UX document (title)
- Technical PRD (title)

**Check:** Extract name from each, compare.

### Feature Traceability
Every "Must Have" in Master Concept should appear in:
- UX flows as documented interactions
- Technical PRD as a Critical User Journey or feature

**Check:** List Must Have items, trace through docs.

### Color Consistency
Brand colors in Brand Kit should be referenced (not redefined) in:
- UX document (color references)
- Technical PRD (design tokens if mentioned)

**Check:** Verify color values match exactly.

### Marketing-to-Core Alignment
Marketing materials must align with Master Concept and Brand Kit:

**Positioning Consistency:**
- Value proposition in positioning-angles.md matches Master Concept
- Target persona in marketing aligns with Target Audience in Master Concept
- Brand personality in positioning matches Brand Kit voice

**Voice Consistency:**
- Copy in direct-response-copy.md follows Voice Codification tone dimensions
- "This, Not That" examples match actual copy patterns
- Microcopy dictionary aligns with direct response copy

**Keyword-to-Product Alignment:**
- Keywords in keyword-research.md relate to actual product features
- SEO topics in seo-content.md connect to Master Concept JTBD

**Check:** Cross-reference marketing files with core documents.

### API Consistency (Implementation Phase)
API endpoints defined in Technical PRD must match:
- Stage architecture files
- Actual frontend API calls

**Check:** Use API validation scripts.

## Auto-Fix Rules

**Safe to auto-fix:**
- Trailing whitespace
- Inconsistent heading levels (# vs ##)
- Missing trailing newline
- Date format standardization

**Never auto-fix:**
- Content differences (names, colors, features)
- Structural issues (missing sections)
- Technical specifications

## Helper Scripts

### Consistency Check Scripts

**Location:** `.shared/scripts/consistency-check/`

| Script | Purpose | Options |
|--------|---------|---------|
| `validate-document-structure.sh` | Check required sections per document type | `--json`, `--quiet` |
| `cross-reference-check.sh` | Check consistency across documents | `--json`, `--quiet` |
| `extract-service-name.sh` | Extract service name from each document | - |

**Example usage:**

```bash
# Check all documents in docs folder
.shared/scripts/consistency-check/validate-document-structure.sh docs/

# Get JSON output for programmatic use
.shared/scripts/consistency-check/cross-reference-check.sh --json docs/

# Quiet mode - only show errors
.shared/scripts/consistency-check/validate-document-structure.sh --quiet docs/
```

**Example output (JSON):**

```json
{
  "status": "fail",
  "results": [
    {"file": "docs/concept/master-concept.md", "status": "pass", "message": "All required sections present", "missing": []},
    {"file": "docs/brand/brand-kit-guide.md", "status": "fail", "message": "Missing sections", "missing": ["Logo", "Typography"]}
  ]
}
```

### API Validation Scripts

**Location:** `.shared/scripts/api-validation/`

| Script | Purpose | Options |
|--------|---------|---------|
| `extract-prd-endpoints.py` | Parse PRD for API endpoints | - |
| `extract-frontend-calls.py` | Parse frontend for API calls | `--base-url`, `--format` |
| `validate-api-contracts.py` | Compare and report discrepancies | `--fuzzy`, `--strict`, `--format` |

**Example usage:**

```bash
# Basic API validation
python3 .shared/scripts/api-validation/validate-api-contracts.py \
  --prd docs/Project-Technical-Architecture.md \
  --frontend src/

# Fuzzy matching (matches /tasks/123 to /tasks/{id})
python3 .shared/scripts/api-validation/validate-api-contracts.py \
  --prd docs/Project-Technical-Architecture.md \
  --frontend src/ \
  --fuzzy

# Markdown report output
python3 .shared/scripts/api-validation/validate-api-contracts.py \
  --prd docs/Project-Technical-Architecture.md \
  --frontend src/ \
  --fuzzy \
  --format markdown
```

**Example output (markdown):**

```markdown
# API Contract Validation Report

**Status:** ⚠️ WARNINGS

## Summary

- PRD Endpoints: 10
- Frontend Calls: 8
- Matched: 8
- Blockers: 0
- Warnings: 2

## ⚠️ Warnings (PRD endpoints not used)

- `GET /api/v1/users/settings`
- `DELETE /api/v1/account`
```

### Supported Frontend Patterns

The `extract-frontend-calls.py` script detects:

- **fetch** - `fetch('/api/...')`, `fetch(\`${baseUrl}/...\`)`
- **axios** - `axios.get()`, `axios.post()`, etc.
- **ky** - Modern fetch wrapper
- **got** - Node.js HTTP client
- **ofetch/$fetch** - Nuxt/Nitro fetch
- **$http** - Angular HTTP client
- **useSWR** - SWR data fetching
- **useQuery** - React Query (v3 and v4)
- **useMutation** - React Query mutations
- **Custom clients** - `api.get()`, `client.post()`

Template literals with common base URL patterns are automatically detected:
- `${API_BASE}`, `${baseUrl}`, `${API_URL}`
- `${process.env.API_URL}`, `${import.meta.env.VITE_API}`

## Integration Points

**Used by:**
- Co-CEO for quality gates
- Quality Checker Agent

**Inputs needed:**
- All documents in `docs/` folder
- Stage files in `docs/stages/`
- Frontend code (for API validation, if exists)

**Outputs:**
- Quality check report
- Auto-fixed files (minor issues)
- Escalation if blockers found

## Troubleshooting

### Script Permissions
If scripts fail to run, ensure they're executable:
```bash
chmod +x .shared/scripts/consistency-check/*.sh
chmod +x .shared/scripts/api-validation/*.py
```

### API Calls Not Detected
If frontend API calls aren't being detected:
1. Check if calls use template literals - they should work now
2. Verify file extensions are `.js`, `.jsx`, `.ts`, `.tsx`, `.vue`, or `.svelte`
3. Check if files are in excluded directories (`node_modules`, `dist`, etc.)
4. Try specifying `--base-url /api/v1` to help resolve variable paths

### Path Parameter Mismatches
If `/tasks/123` isn't matching `/tasks/{id}`:
1. Use `--fuzzy` flag for automatic parameter detection
2. The script recognizes: UUIDs, numeric IDs, and 6-24 char alphanumeric IDs

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Name mismatch | Updated in one doc, not others | Search-replace across all docs |
| Missing section | Template not followed | Add section, populate |
| Inconsistent colors | Copy-paste error | Reference Brand Kit hex values |
| Feature gap | Scope creep or oversight | Add to Master Concept or remove from implementation |
| API mismatch | Frontend/backend independent dev | Sync endpoints, update PRD as source of truth |
