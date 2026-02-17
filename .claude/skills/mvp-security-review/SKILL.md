---
name: mvp-security-review
description: Use when conducting security reviews for MVP/startup web applications, SaaS products, or software before launch. Apply when assessing authentication, API security, frontend protections, data storage, supply chain, or creating security remediation plans.
---

# MVP Security Review

## Overview

Conduct security reviews right-sized for MVPs—addressing existential risks without enterprise overhead.

**Core principle:** Minimum Viable Security (MVS) focuses on vulnerabilities that could cause immediate insolvency, massive data theft, or irreversible reputational damage, while deliberately deferring advanced controls.

## When to Use

**Use this skill when:**
- Reviewing security posture before MVP launch
- Assessing authentication/authorization implementation
- Reviewing API security controls
- Checking frontend security (XSS, CSP, CORS)
- Auditing data storage and secrets management
- Scanning for supply chain vulnerabilities
- Creating security remediation plans

**Don't use for:**
- Full enterprise security audits (SOC 2, ISO 27001)
- Professional penetration testing
- Compliance frameworks requiring certification

## Example Scenarios

**Pre-launch Review:**
```
User: "We're launching our SaaS MVP next week. Can you review security?"
→ Invoke mvp-security-review skill for comprehensive review
```

**Post-Implementation Check:**
```
User: "I just implemented user authentication. Is it secure?"
→ Invoke mvp-security-review skill (focused on AuthN/AuthZ sections)
```

**Dependency Audit:**
```
User: "Need to check if our dependencies have vulnerabilities"
→ Invoke mvp-security-review skill (focused on supply chain)
```

## The Four Review Phases

### Phase 1: Context & Threat Modeling

Before reviewing code, understand the "Crown Jewels":

1. **Entry Points:** Where can attackers interact? (APIs, Login, Webhooks)
2. **Assets:** What are they targeting? (DB credentials, User data, PII)
3. **Controls:** What currently stops them? (WAF, Auth, VPCs)

### Phase 2: Automated Reconnaissance

Run automated scans to establish baseline:

```bash
# Run the security scan helper script
.shared/scripts/security-scan.sh [project-path]
```

This runs SAST, secret scanning, and dependency checks.

### Phase 3: Manual Architectural Inspection

Review business logic that automated tools miss:

| Area | Check | Common Vulnerability |
|------|-------|---------------------|
| AuthN | Session tokens in HttpOnly cookies? | XSS token theft |
| AuthZ | Server-side ownership checks? | BOLA/IDOR |
| API | Input validation with DTOs/schemas? | Mass assignment |
| Data | Database network isolated? | Public exposure |
| Secrets | Environment variables, not hardcoded? | Credential leaks |

### Phase 4: Remediation & Sign-off

Prioritize findings:
- **Blocker:** Risk too high to release
- **Conditional Pass:** Fix within 7 days post-launch
- **Deferred:** Track for post-MVP hardening

## Severity Classification Guide

Use this to classify findings consistently:

**Blocker (Fix Before Launch)**
- **Test:** "Could this lead to massive data breach or total system compromise?"
- **Examples:** RCE (eval, command injection), SQL injection, exposed secrets, broken authentication, hardcoded credentials
- **Impact:** Immediate insolvency, massive data theft, irreversible reputational damage

**Conditional Pass (Fix Within 7 Days)**
- **Test:** "Does this make attacks easier but not enable completely new attack vectors?"
- **Examples:** Missing rate limiting, permissive CORS, missing security headers, weak CSRF protection
- **Impact:** Increases risk of brute force, enumeration, or DoS attacks

**Deferred (Post-MVP Hardening)**
- **Test:** "Would enterprise customers expect this for compliance?"
- **Examples:** No WAF, no bug bounty, missing SIEM, no penetration test, no SOC 2
- **Impact:** Competitive/sales disadvantage, not existential risk

## Security Review Checklist

Use this as your systematic review guide. Copy and check off items:

### Authentication & Identity

- [ ] Using established IdP (Auth0, Supabase, Firebase) OR bcrypt/Argon2id for passwords
- [ ] Session tokens stored in HttpOnly, Secure, SameSite cookies (NOT localStorage)
- [ ] Access tokens have short expiration (15-60 min)
- [ ] Refresh token rotation implemented
- [ ] No MD5, SHA-1, or plain text password storage

### Authorization

- [ ] Server-side authorization on EVERY endpoint
- [ ] BOLA/IDOR prevention: ownership checks on resource access
- [ ] RBAC middleware enforced (not just frontend hiding)
- [ ] Admin endpoints tested as non-admin user

### API Security

- [ ] Input validation with DTOs/schemas (Zod, Joi, Pydantic)
- [ ] No mass assignment vulnerabilities
- [ ] No raw SQL/NoSQL queries with user input
- [ ] Parameterized queries only
- [ ] Rate limiting on login, register, password-reset (5 req/min)
- [ ] Global rate limiting (100 req/min per IP)
- [ ] Generic error messages in production (no stack traces)

### Frontend Security

- [ ] No `dangerouslySetInnerHTML` (React) / `v-html` (Vue) with unsanitized input
- [ ] If used, DOMPurify sanitization applied
- [ ] Content-Security-Policy header configured
- [ ] `object-src: 'none'` and `base-uri: 'self'` in CSP
- [ ] CORS restricted to specific domains (no `*` with credentials)

### Data & Infrastructure

- [ ] Database NOT publicly accessible (private subnet/VPC)
- [ ] Encryption at rest enabled
- [ ] TLS/SSL enforced for database connections
- [ ] Secrets in environment variables (not source code)
- [ ] `.env` files in `.gitignore`
- [ ] Automated daily backups configured
- [ ] Backup restore tested

### Supply Chain

- [ ] No Critical/High CVEs in dependencies
- [ ] Dependabot or equivalent enabled
- [ ] Secret scanning on commit history (TruffleHog/git-secrets)

### Documentation & Response

- [ ] Vulnerability disclosure policy exists (security.txt or /security page)
- [ ] Basic incident response plan documented
- [ ] Incident Commander and PR roles assigned

## Quick Reference: Security Headers

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
```

## Quick Reference: Recommended Tools

| Category | Tool | Purpose |
|----------|------|---------|
| SAST | Semgrep | Code pattern scanning |
| Secrets | TruffleHog | Commit history scanning |
| SCA | Dependabot / npm audit | Dependency vulnerabilities |
| DAST | OWASP ZAP | Web application scanning |
| WAF | Cloudflare (Free) | DDoS/basic protection |
| IdP | Auth0 / Supabase Auth | Authentication |

## Deferrable Items (Post-MVP)

| Control | Defer Until |
|---------|-------------|
| SOC 2 / ISO 27001 | ~$1M ARR or enterprise customers |
| Full Penetration Test | v1.0 release or payments feature |
| SIEM / 24/7 SOC | Dedicated DevOps/Security staff |
| Bug Bounty Program | Post-Series A maturity |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| JWT in localStorage | Use HttpOnly cookies |
| `Access-Control-Allow-Origin: *` | Whitelist specific domains |
| Hiding admin features in frontend only | Server-side RBAC middleware |
| Raw SQL queries | Use ORM with parameterized queries |
| Secrets in source code | Environment variables + secrets manager |
| Database publicly accessible | Private subnet, bastion host access |

## Review Report Template

After completing the review, document findings:

```markdown
# Security Review Report - [Project Name]

**Date:** YYYY-MM-DD
**Reviewer:** [Name/Agent]
**Scope:** [MVP Pre-launch Review]

## Executive Summary
[1-2 sentences on overall security posture]

## Findings

### Blockers (Fix Before Launch)
1. [Finding with severity and remediation]

### Conditional Pass (Fix Within 7 Days)
1. [Finding with severity and remediation]

### Deferred (Post-MVP Hardening)
1. [Item for future improvement]

## Automated Scan Results
[Output from security-scan.sh]

## Recommendations
[Prioritized list of next steps]

## Sign-off
[ ] Blockers resolved
[ ] Conditional items tracked
[ ] Residual risk accepted by: [CTO/Architect]
```

## Integration with Other Skills

- **verification-before-completion:** Run security scans before claiming review complete
- **test-driven-development:** Write security tests for auth/authz flows
- **writing-plans:** Create remediation plan for complex fixes

## The Bottom Line

Focus on existential risks:
1. Can attackers become admin? (AuthN/AuthZ)
2. Can they steal all user data? (BOLA, Injection)
3. Can they steal credentials? (Secrets, XSS)
4. Can they take down the service? (DoS, Rate limiting)

Fix these first. Defer enterprise controls until you have enterprise customers.
