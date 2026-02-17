---
name: phase-4-2-user-approval
description: Co-CEO Phase 4.2 - Present summary of completed work, get user approval, and guide template selection. CRITICAL GATE - requires explicit user approval.
---

# Phase 4.2: User Approval & Template Selection

**Mode:** Conversational with main user  
**Skill to use:** `template-selector`  
**Model:** Opus (Co-CEO Session)  
**Depends on:** Phase 4.1 (or skip if no Notion)

## CRITICAL GATE

This phase requires **explicit user approval** before proceeding. Do not bypass.

## Status Communication

Announce:
> "Now reviewing everything we've created before moving to template selection and implementation."

## Process

### 1. Present Summary

```
Here's what we've completed:

**Master Concept:**
- Problem: [1-2 sentences]
- Target audience: [1 sentence]
- Key features: [3-5 bullets]

**Brand Identity:**
- Visual: [Colors, typography, logo direction]
- Voice & tone: [Describe personality]
- Name & domain: [Official name, domain]

**User Experience:**
- Key workflows: [List critical journeys]
- Design approach: [Web/mobile, style notes]

**Technical Architecture:**
- Tech stack: [Database, backend, frontend]
- Implementation stages: [List stages with estimates]
```

### 2. Ask Approval Questions

- "Does this match your vision?"
- "Any changes or concerns before template selection?"
- "Ready to proceed?"

### 3. Template Selection (after approval)

Present the 3 available templates:
- **Analytics Dashboard** - Data visualization, metrics, reporting
- **Productivity Tool** - Task management, project collaboration
- **Content Creator** - Content creation, scheduling, publishing

Use `template-selector` skill for detailed analysis.

**Security gate:** confirm the chosen template has no BLOCKER issues from `template-validator` (especially Supabase schema/RLS/search_path checks) before finalizing selection.

### 4. Record Template Selection

After user selects a template, create the selection file:

```bash
mkdir -p docs
echo "[template-name]" > docs/selected-template.txt
git add docs/selected-template.txt
```

Where `[template-name]` is one of: `analytics-dashboard`, `productivity-tool`, `content-creator`, `utility-processor`, or `digital-download`

### 5. Offer Session Break (Optional)

After template selection and recording, present:

```
Template selection complete! This is another natural break point.

**Option to Refresh Session:**
We've completed design and planning (Phases 1-4). Implementation is next (template integration and stage execution).

You can:
- **Continue this session** and proceed to Phase 4.3 (Template Integration)
- **Start fresh Co-CEO session** with clean context window for implementation

A fresh session can be helpful before the implementation phase. If you'd like to start fresh, I'll provide a ready-made prompt to continue from Phase 4.3.

Which would you prefer?
```

### 6. If User Chooses Fresh Session

Provide the continuation prompt:

```
Perfect! Here's how to start a fresh Co-CEO session:

1. First, commit the template selection:
   ```bash
   git add docs/selected-template.txt
   git commit -m "Phase 4.2: Template selection complete"
   git push origin main
   ```

2. Start a new Co-CEO session and use this prompt:

---

**PROMPT FOR NEW CO-CEO SESSION:**

"I'm continuing MVP development from Phase 4.3 (Template Integration). Phases 1-4.2 are complete.

Current project state:
- ✅ Concept & Brand (Phase 1)
- ✅ Design & Architecture (Phase 2-3)
- ✅ Planning complete (Phase 4.1-4.2)
- ✅ Template selected: [check docs/selected-template.txt]

Please:
1. Verify phase completion:
```bash
.shared/scripts/co-ceo/verify-phase-completion.sh --list
```

2. Read template selection:
```bash
cat docs/selected-template.txt
```

3. Proceed to Phase 4.3 (Template Integration):
```bash
.shared/scripts/co-ceo/load-phase-context.sh 4.3
```

Let's integrate the template and start building!"

---

When you're ready, just start that new session and paste the prompt above.
```

### 7. If User Chooses to Continue

```
Great! Continuing with this session. Let me load Phase 4.3 context...
```

Then proceed directly to Phase 4.3.

## Completion Criteria

- [ ] User explicitly approves Phase 1-2 work
- [ ] Template selected and confirmed
- [ ] Selection documented in `docs/selected-template.txt`
- [ ] File committed to git (if continuing) or instructions given (if new session)
- [ ] Session option presented and user choice recorded

**Do not proceed until user says yes AND selects a template.**

## Important Notes

- **Always record template selection** to `docs/selected-template.txt` for session continuity
- **No forcing:** Never require the user to start a new session
- **Clear benefit:** Explain that fresh context helps before implementation
- **Ready-made prompt:** Provide complete, copy-paste ready instructions

## Verify Before Proceeding

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 4.2
```
