# Stage Architecture Template

Use this template when creating detailed architecture plans for each implementation stage. Each stage should have its own file following this structure.

---

# Stage [NN]: [Stage Name]

**Status:** Planned | In Progress | Complete | Blocked  
**Estimated Duration:** [X-Y hours]  
**Assigned Agent:** [Agent name or "Unassigned"]  
**Last Updated:** [Date]

---

## 1. Overview

*What this stage accomplishes. One paragraph summary.*

**Delivers:**
- [Bullet list of concrete deliverables]

**Success Criteria:**
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]

---

## 2. Dependencies

### Must Complete First
| Stage | Status | What We Need |
|-------|--------|--------------|
| Stage [N] | ✅/🔄/❌ | [Specific dependency] |

### Can Run In Parallel
- Stage [N]: [Name] - no conflicts
- Stage [N]: [Name] - shared [X] but independent changes

### Blocks These Stages
- Stage [N]: [Name] - depends on [what we produce]

---

## 3. Technical Components

### 3.1 [Component Category 1]

*Describe what will be built.*

```
[Code snippets, schemas, or configuration as needed]
```

### 3.2 [Component Category 2]

*Continue for each major component.*

---

## 4. API Contracts (if applicable)

*Skip this section if stage doesn't involve API work.*

### Endpoints Created

#### [HTTP Method] /api/v1/[endpoint]

**Purpose:** [What this endpoint does]

**Request:**
```json
{
  "field": "type (required/optional)"
}
```

**Response (2XX):**
```json
{
  "field": "type"
}
```

**Errors:**
| Code | Condition | Response |
|------|-----------|----------|
| 400 | [Condition] | `{"error": "message"}` |
| 401 | [Condition] | `{"error": "message"}` |

### Endpoints Consumed

*List any existing endpoints this stage calls.*

| Endpoint | Purpose | Stage That Creates It |
|----------|---------|----------------------|
| [Endpoint] | [Purpose] | Stage [N] |

---

## 5. Database Schema Changes (if applicable)

*Skip this section if no database changes.*

### Tables Created

```sql
CREATE TABLE public.[table_name] (
  -- Schema definition
);

ALTER TABLE public.[table_name] ENABLE ROW LEVEL SECURITY;

CREATE POLICY "[policy_name]" ON public.[table_name]
FOR [SELECT/INSERT/UPDATE/DELETE/ALL] USING (
  -- Policy definition
);
```

### Tables Modified

| Table | Change | Migration |
|-------|--------|-----------|
| [table] | [What changes] | [Migration file name] |

### Indexes Added

```sql
CREATE INDEX [index_name] ON public.[table]([columns]);
```

---

## 6. Testing Requirements

### Unit Tests

| Test | What It Validates |
|------|------------------|
| `test_[name]` | [Description] |
| `test_[name]` | [Description] |

### Integration Tests

| Test | What It Validates |
|------|------------------|
| `test_[name]` | [Description] |

### Manual Verification

- [ ] [Manual check 1]
- [ ] [Manual check 2]

---

## 7. Critical Constraints

**DO NOT:**
- [Explicit constraint 1]
- [Explicit constraint 2]

**MUST:**
- [Required behavior 1]
- [Required behavior 2]

---

## 8. Progress Log

*Updated by implementing agent during work.*

### [Date] - [Time]
- **Completed:** [What was done]
- **Next:** [What's planned]
- **Blockers:** [Issues or "None"]

---

## 9. Issues & Blockers

*Document any escalations here.*

### [Issue Title] - [Status: Open/Resolved]

**Date:** [When discovered]  
**Severity:** Blocker | Warning

**Description:**
[Clear description of the issue]

**Attempts Made:**
1. [Attempt 1]: [Result]
2. [Attempt 2]: [Result]
3. [Attempt 3]: [Result]

**Error Logs:**
```
[Relevant error output]
```

**Resolution:**
[How it was resolved, or "Escalated to Co-CEO"]

---

## 10. Completion Checklist

- [ ] All components built per Section 3
- [ ] All API contracts implemented per Section 4
- [ ] All database changes applied per Section 5
- [ ] All tests passing per Section 6
- [ ] All constraints followed per Section 7
- [ ] Progress log updated per Section 8
- [ ] Success criteria met (Section 1)
- [ ] Verified using `verification-before-completion` skill

**Stage Completed:** [Date] | **Final Status:** [Complete/Blocked]

---

*Template version: 1.0*
