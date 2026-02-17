---
name: phase-6-9-build-verification
description: Use when implementation and security review are complete and you must prove the MVP is deployable with clean installs, builds, and tests before handoff.
---

# Phase 6.9: Build Verification Gate

**Mode:** Conversational with main user  
**Model:** Opus (Co-CEO Session)  
**Depends on:** Phase 6.1 and Phase 6.2 complete  
**Blocking Gate:** Do not proceed to Phase 7.1 without passing this phase

## Purpose

The Co-CEO process can only claim deployability after running the same clean build and test steps a deployment pipeline would run. This phase provides evidence that:

- Dependencies install cleanly
- Builds succeed without missing imports
- Tests (if present) pass
- TypeScript compiles where configured

## Status Communication

Announce:
> "Before we hand off, I need to run the build verification gate. This proves the app can install, build, and test cleanly. I’ll capture evidence in a report."

## Inputs

- Template selected in `docs/selected-template.txt`
- Implementation output from Phase 6.1
- Security review completed in Phase 6.2

## Verification Workflow

### 1. Identify Project Paths

Determine the frontend root from the selected template:

```bash
cat docs/selected-template.txt
```

Then set:
```
SELECTED_TEMPLATE=$(cat docs/selected-template.txt)
TEMPLATE_PATH="templates/$SELECTED_TEMPLATE/frontend"
```

Capture project root:
```
PROJECT_ROOT=$(pwd)
```

### 2. Clean Install

```bash
cd "$TEMPLATE_PATH"
rm -rf node_modules
npm install
```

### 3. Build + Tests

Run available scripts in this order:

```bash
npm run build
npm test    # Only if package.json defines "test"
npm run lint # Only if package.json defines "lint"
```

If TypeScript is configured, run:

```bash
npx tsc --noEmit
```

### 4. Document Results

Create the report:

```bash
cat > "$PROJECT_ROOT/docs/build-verification-report.md" << EOF
# Build Verification Report (Phase 6.9)

**Date:** $(date -u +%Y-%m-%dT%H:%M:%SZ)  
**Template:** $SELECTED_TEMPLATE  
**Frontend Path:** $TEMPLATE_PATH  

## Commands Executed

- `npm install` (clean)
- `npm run build`
- `npm test` (only if defined)
- `npm run lint` (only if defined)
- `npx tsc --noEmit` (only if tsconfig exists)

## Results

- Install: PASS/FAIL
- Build: PASS/FAIL
- Tests: PASS/FAIL/NOT RUN
- Lint: PASS/FAIL/NOT RUN
- TypeScript: PASS/FAIL/NOT RUN

## Notes

- Any failures and remediation steps documented here.
EOF
```

Update PASS/FAIL statuses with actual outcomes before saving.

### 5. Gate Outcome

- If all required commands pass → proceed to Phase 7.1
- If any required command fails → stop, remediate, and re-run

## Completion Criteria

- [ ] Clean install completed
- [ ] Build completed successfully
- [ ] Tests executed (if defined) and passing
- [ ] Lint executed (if defined) and passing
- [ ] TypeScript compile check executed (if configured) and passing
- [ ] `docs/build-verification-report.md` created with evidence

## Verify

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 6.9
```
