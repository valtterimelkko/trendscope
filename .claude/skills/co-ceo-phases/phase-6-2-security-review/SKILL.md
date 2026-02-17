---
name: phase-6-2-security-review
description: Co-CEO Phase 6.2 - Launch Security Review agent to conduct comprehensive security audit of implemented code. Simple fixes applied directly; significant issues escalated. Kimi Code CLI compatible.
---

# Phase 6.2: Security Review

**Mode:** Agent  
**Skill to use:** `mvp-security-review`  
**Complexity:** Critical (deep security analysis required)  
**Platform:** Kimi Code CLI  
**Depends on:** Phase 4.3.5 Supabase security audit PASS + Phase 5.1 architecture check  
**Timing:** Run **before Stage Execution begins** and re-run after major implementation changes

## Status Communication

Announce:
> "Launching Security Review agent. This conducts a comprehensive security audit (auth, APIs, frontend protections, data storage, dependencies) **before implementation begins**. Complex analysis—may take 15-30 minutes."

## Agent Instructions (Kimi Task Tool Format)

```python
Task(
    description="Security Review - Comprehensive security audit",
    subagent_name="coder",
    prompt="""
You are a Security Review agent. Use the mvp-security-review skill.

COMPLEXITY: critical — This task requires deep security analysis, threat modeling, and comprehensive audit of all system components.

TASK:
Conduct comprehensive security review of:
1. Authentication implementation
2. API security (auth, rate limiting, input validation)
3. Frontend protections (XSS, CSRF)
4. Data storage security
5. Supply chain (dependencies)
6. Secrets management
7. Confirm Supabase hardening from Phase 4.3.5 remains PASS (all SECURITY DEFINER functions set `search_path = 'public'`; RLS enforced on public tables). If new migrations/functions were added, **re-run** `.shared/scripts/supabase/security-audit.sh`.

INPUTS:
- All code in the repository
- docs/Project-Technical-Architecture.md
- docs/stages/*.md

OUTPUTS:

If simple fixes needed:
- Implement fixes directly
- Document what was fixed

If significant changes needed:
- Create docs/security-remediation-plan.md
- Escalate to Co-CEO Session for user awareness
- Do NOT implement large changes without approval

CONSTRAINTS:
- Do NOT spawn additional agents
- Bring ALL findings to user attention via Co-CEO Session
"""
)
```

## Completion Criteria

- [ ] All 7 security areas reviewed (includes Supabase hardening check)
- [ ] Simple fixes implemented
- [ ] Complex issues documented in remediation plan (if any)
- [ ] User notified of any significant findings

## After Agent Completes

```bash
.shared/scripts/co-ceo/git-commit-phase.sh "6.2" "Security review completed"
```

Display findings summary to user:
> "Security review complete. [Summary of findings]. [Any remediation required]."

## Verify

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 6.2
```
