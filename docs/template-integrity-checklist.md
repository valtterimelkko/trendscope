# Template Integrity Checklist

This document defines what features and pages should exist in each MVP template to prevent contamination between templates.

## Core Principle

Each template must have its own distinct, minimal feature set that matches its specific use case. Templates should NOT share features that are specific to other templates' use cases.

## Template Feature Matrix

### 1. Digital Download Portal

**Purpose:** Selling and delivering downloadable file packs (design kits, LUTs, presets, PDF bundles)

**Dashboard Pages:**
- ✅ `/dashboard` - Download locker (main page)
- ✅ `/settings/general` - Account settings
- ✅ `/settings/billing` - Billing management
- ❌ NO calendar, queue, media library, analytics, or social connections

**Sidebar Navigation:**
- Downloads (main)
- Settings (bottom)

**Key Components:**
- Download locker with file list
- Usage/quota meter (downloads count)
- Order history
- Signed URL delivery

**Data Model:**
- Single-user (no workspaces/teams)
- Downloads tracking
- Subscription tiers based on download limits

---

### 2. Content Creator

**Purpose:** Content management and publishing platform for creators, writers, and media teams

**Dashboard Pages:**
- ✅ `/dashboard` - Content library
- ✅ `/dashboard/queue` - Publishing queue
- ✅ `/dashboard/calendar` - Content calendar
- ✅ `/dashboard/media` - Media library
- ✅ `/dashboard/connect` - Social media connections
- ✅ `/dashboard/analytics` - Content analytics
- ✅ `/settings/general` - Account settings
- ✅ `/settings/billing` - Billing management
- ✅ `/settings/team` - Team management

**Sidebar Navigation:**
- Content
- Queue
- Calendar
- Analytics
- Media
- Connect
- Settings (bottom)

**Key Components:**
- Rich text editor (TipTap)
- Media uploader
- Content calendar
- Social account connections

**Data Model:**
- Multi-tenant workspaces
- Posts with status workflow
- Team members with roles
- Scheduled publishing

---

### 3. Analytics Dashboard

**Purpose:** Data analytics and visualization for tracking metrics and events

**Dashboard Pages:**
- ✅ `/dashboard` - Analytics overview
- ✅ `/dashboard/public` - Public dashboard settings
- ✅ `/settings/general` - Account settings
- ✅ `/settings/billing` - Billing management
- ✅ `/settings/snippet` - Tracking code/embed
- ❌ NO content creation, calendars, or media libraries

**Sidebar Navigation:**
- Dashboard
- Public Dashboards
- Settings (bottom)

**Key Components:**
- Chart/graph components
- Real-time metrics
- Event tracking
- Embed code generation

**Data Model:**
- Usage-based billing (events/month)
- Public dashboard sharing
- Event storage and aggregation

---

### 4. Productivity Tool

**Purpose:** Task and project management for individuals and teams

**Dashboard Pages:**
- ✅ `/dashboard` - Task/project list
- ✅ `/settings/general` - Account settings
- ✅ `/settings/billing` - Billing management
- ✅ `/settings/team` - Team management
- ❌ NO publishing features, calendars (unless task scheduling), or media libraries

**Sidebar Navigation:**
- Tasks/Projects
- Settings (bottom)

**Key Components:**
- Task list/board
- Quick actions
- Keyboard shortcuts
- SidePeek detail view

**Data Model:**
- Seat-based billing (per team member)
- Task/project hierarchy
- Team collaboration

---

### 5. Utility Processor

**Purpose:** File upload, processing, and download workflows (converters, resizers, etc.)

**Dashboard Pages:**
- ✅ `/dashboard` - Processing interface
- ✅ `/dashboard/history` - Job history/logs
- ✅ `/settings/general` - Account settings
- ✅ `/settings/billing` - Billing management
- ❌ NO content creation, social features, or collaboration

**Sidebar Navigation:**
- Process
- History
- Settings (bottom)

**Key Components:**
- Upload interface
- Processing status
- Download results
- Job queue

**Data Model:**
- Usage-based or credit-based billing
- Processing jobs
- File storage with expiration

---

## Validation Process

When creating or modifying a template:

### 1. Feature Audit
- [ ] List all dashboard pages
- [ ] Compare against template feature matrix
- [ ] Remove any pages that don't belong to this template's use case

### 2. Component Audit
- [ ] List all dashboard components
- [ ] Verify each component is necessary for this template's use case
- [ ] Remove components borrowed from other templates

### 3. Data Model Audit
- [ ] Review database schema
- [ ] Verify it matches the template's use case
- [ ] Remove tables/fields for features from other templates

### 4. Sidebar Navigation Audit
- [ ] Check sidebar navigation items
- [ ] Ensure they match the template feature matrix
- [ ] Remove navigation to pages that don't exist or shouldn't exist

### 5. Documentation Audit
- [ ] Review README.md feature list
- [ ] Verify manifest.json features array
- [ ] Ensure documentation matches actual implementation

## Common Contamination Patterns

### ❌ Anti-Patterns to Avoid:

1. **Content Creator features in non-content templates**
   - Publishing calendar
   - Publishing queue
   - Social media connections
   - Rich text editor
   - Media library

2. **Multi-tenant features in single-user templates**
   - Workspace selector
   - Team management
   - Workspace members

3. **Analytics features in non-analytics templates**
   - Complex charts and graphs
   - Event tracking
   - Public sharing

4. **Processing features in non-utility templates**
   - File upload/processing queues
   - Job history
   - Format conversion

## How This Contamination Happened

The digital-download template was likely scaffolded using the content-creator template as a base, and the content-creator-specific features were not properly removed. This can happen when:

1. Copy-pasting code between templates
2. Using one template as a starting point for another
3. Not following the feature matrix during scaffolding
4. Insufficient cleanup after initial scaffolding

## Prevention Strategies

1. **Use Template Matrix as Source of Truth**
   - Always reference this document before adding features
   - Question any feature that's not in the matrix

2. **Independent Scaffolding**
   - Build each template from scratch based on its use case
   - Avoid copy-pasting large sections between templates

3. **Regular Audits**
   - Periodically review templates against this matrix
   - Remove contamination as soon as it's discovered

4. **Clear Documentation**
   - Document the purpose of each template clearly
   - Reference this matrix in template READMEs

5. **Automated Checks**
   - Create scripts to detect common contamination patterns
   - Validate templates before deployment

## Template Integrity Check Script

To check a template for contamination:

```bash
# Check for content-creator contamination in digital-download
find templates/digital-download -type f -name "*.tsx" | xargs grep -l "RichTextEditor\|MediaUploader\|ContentCalendar\|workspace"

# Check for unexpected dashboard pages
ls -la templates/digital-download/frontend/app/\(dashboard\)/dashboard/

# Expected output: only page.tsx (the main dashboard page)
```

## Conclusion

Maintaining template integrity is critical for:
- User experience (users get exactly what they need, nothing more)
- Maintainability (less code to maintain)
- Performance (smaller bundle sizes)
- Clarity (templates are easier to understand)

Always validate templates against this matrix before deployment.
