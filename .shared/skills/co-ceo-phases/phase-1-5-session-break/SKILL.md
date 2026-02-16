---
name: phase-1-5-session-break
description: Co-CEO Phase 1.5 - Optional session break and context refresh. Suggest fresh Co-CEO session to manage context window after completing foundation work.
---

# Phase 1.5: Session Break (Optional)

**Mode:** Conversational with main user  
**Depends on:** Phase 1.4 complete  
**Optional:** User can choose to continue or start fresh session

## Purpose

After completing Phase 1 (Concept & Brand foundation), this is a natural stopping point where:
- The user may want to take a break
- A fresh Co-CEO session with a clean context window can be beneficial
- All foundation documents are complete and committed to git

## Status Communication

Announce:
> "Phase 1 complete! We've finished the Concept & Brand foundation (Master Concept, Brand Kit, Naming, and Marketing Foundation). This is a natural break point.
> 
> **Option to Refresh Session:**
> You can continue with this session, or start a fresh Co-CEO session with a clean context window. A fresh session can be helpful after orchestrating multiple phases.
> 
> If you'd like to start fresh, I'll provide you with a ready-made prompt to continue from Phase 2."

## Process

### 1. Summary of Completed Work

Present what's been accomplished:

```
✅ Phase 1.1: Master Concept refined
✅ Phase 1.2: Brand Kit & Guide created  
✅ Phase 1.3: Service name & domain selected
✅ Phase 1.4: Marketing Foundation complete
   - Positioning angles
   - Keyword research
   - Lead magnet strategy
   - Direct response copy
   - Brand voice codification
   - SEO content plan

All documents are committed to git. Ready to push to GitHub.
```

### 2. Offer Session Options

```
You have two options:

**Option A: Continue This Session**
- We'll proceed directly to Phase 2 (UX Design & Technical Architecture)
- Current context window remains

**Option B: Start Fresh Co-CEO Session**
- Clean context window for better performance
- You can take a break before continuing
- I'll provide the exact prompt to resume at Phase 2

Which would you prefer?
```

### 3. If User Chooses Fresh Session

Provide the continuation prompt:

```
Perfect! Here's how to start a fresh Co-CEO session:

1. Push your current work to GitHub:
   ```bash
   git push origin main
   ```

2. Start a new Co-CEO session and use this prompt:

---

**PROMPT FOR NEW CO-CEO SESSION:**

"I'm continuing MVP development from Phase 2. Phase 1 (Concept & Brand) is complete.

Current project state:
- ✅ Master Concept: docs/concept/master-concept.md
- ✅ Brand Kit: docs/brand/brand-kit-guide.md
- ✅ Marketing Foundation: marketing/*.md (6 deliverables)

Please verify phase completion with:
```bash
.shared/scripts/co-ceo/verify-phase-completion.sh --list
```

Then proceed to Phase 2.1 (MVP UX Design). Load the phase context with:
```bash
.shared/scripts/co-ceo/load-phase-context.sh 2.1
```

Let's continue building this MVP!"

---

When you're ready, just start that new session and paste the prompt above.
```

### 4. If User Chooses to Continue

```
Great! Continuing with this session. Let me load Phase 2.1 context...
```

Then proceed directly to Phase 2.1.

## Important Notes

- **No forcing:** Never require the user to start a new session
- **Clear benefit:** Explain that fresh context helps with performance
- **Ready-made prompt:** Provide complete, copy-paste ready instructions
- **Git safety:** Ensure all work is committed before suggesting session change

## Completion Criteria

- [ ] Phase 1 completion summary presented
- [ ] Session options explained
- [ ] If fresh session: Continuation prompt provided
- [ ] If continue: Proceeding to Phase 2.1

## After This Phase

No git commit needed (already done in Phase 1.4).

### If Continuing This Session:
```bash
.shared/scripts/co-ceo/load-phase-context.sh 2.1
```

### If User Starts Fresh Session:
The new Co-CEO session will handle Phase 2.1 startup.

## Verify Before Proceeding

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 1.4
```

Phase 1.5 itself has no deliverables—it's a coordination point.
