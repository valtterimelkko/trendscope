# Template Integrity - Quick Reference Guide

**For agents and developers maintaining the MVP meta-project templates.**

---

## 🎯 The Golden Rule

**Each template must contain ONLY features that match its specific use case.**

Never copy features between templates without checking the integrity matrix.

---

## 📋 Quick Feature Matrix

| Template | Key Features | What's NOT Included |
|----------|-------------|---------------------|
| **Digital Download** | Downloads, Billing, Settings | ❌ Calendar, Queue, Media, Social, Analytics, Teams |
| **Content Creator** | Posts, Queue, Calendar, Media, Social, Analytics | ✅ All content features |
| **Analytics Dashboard** | Charts, Metrics, Public Dashboards | ❌ Content creation, Publishing, Media |
| **Productivity Tool** | Tasks, Projects, Team | ❌ Publishing, Social, Media library |
| **Utility Processor** | Upload, Process, Download, History | ❌ Content creation, Teams, Publishing |

---

## 🚨 Quick Contamination Check

Run these commands before deploying any template:

### Digital Download
```bash
# Should return ONLY page.tsx:
ls templates/digital-download/frontend/app/\(dashboard\)/dashboard/

# Should return EMPTY:
find templates/digital-download -name "*.tsx" | xargs grep -l "RichTextEditor\|MediaUploader\|ContentCalendar\|workspace"
```

### Analytics Dashboard
```bash
# Should NOT have content pages:
ls templates/analytics-dashboard/frontend/app/\(dashboard\)/dashboard/

# Should NOT have content components:
find templates/analytics-dashboard -name "*.tsx" | xargs grep -l "RichTextEditor\|MediaUploader\|queue"
```

### Productivity Tool
```bash
# Should NOT have publishing pages:
ls templates/productivity-tool/frontend/app/\(dashboard\)/dashboard/ | grep -E "queue|calendar|connect|media"

# Should return EMPTY
```

---

## ✅ Validation Checklist

Before committing changes to any template:

- [ ] Run `ls -la templates/{name}/frontend/app/\(dashboard\)/dashboard/`
- [ ] Verify pages match the feature matrix
- [ ] Check for components from other templates
- [ ] Review sidebar navigation items
- [ ] Verify data model (single-user vs multi-tenant)
- [ ] Update README.md if features changed
- [ ] Update manifest.json if features changed

---

## 🔍 Common Contamination Signs

**Digital Download contaminated if it has:**
- ❌ `dashboard/calendar/` directory
- ❌ `dashboard/queue/` directory
- ❌ `dashboard/media/` directory
- ❌ `dashboard/connect/` directory
- ❌ `dashboard/analytics/` directory
- ❌ `settings/team/` directory
- ❌ `RichTextEditor.tsx` component
- ❌ `MediaUploader.tsx` component
- ❌ `ContentCalendar.tsx` component
- ❌ Workspace-related props in Sidebar

**Analytics Dashboard contaminated if it has:**
- ❌ Rich text editing features
- ❌ Publishing calendar
- ❌ Media upload features
- ❌ Social connections

**Productivity Tool contaminated if it has:**
- ❌ Publishing queue
- ❌ Content calendar (unless task scheduling)
- ❌ Social media features
- ❌ Rich text content editing

---

## 📚 Full Documentation

For complete details, see:

1. **`docs/template-integrity-checklist.md`**
   - Complete feature matrix for all 5 templates
   - Detailed validation procedures
   - Prevention strategies

2. **`docs/template-contamination-fix-summary.md`**
   - Case study of digital-download cleanup
   - Root cause analysis
   - Lessons learned

3. **`docs/template-cleanup-before-after.md`**
   - Visual comparison of cleanup
   - Sidebar navigation details
   - File-level changes

4. **`.shared/skills/template-scaffolding/SKILL.md`**
   - Guidelines for creating templates
   - Integrity principles

5. **`.shared/skills/template-validator/SKILL.md`**
   - Validation procedures
   - Automated checks

---

## 🛠️ Quick Fixes

### If you find contamination:

1. **Identify contaminated files:**
   ```bash
   find templates/{name} -name "*.tsx" | xargs grep -l "{ContaminatedComponent}"
   ```

2. **Remove contaminated pages:**
   ```bash
   rm -rf templates/{name}/frontend/app/\(dashboard\)/dashboard/{page}/
   ```

3. **Remove contaminated components:**
   ```bash
   rm templates/{name}/frontend/components/dashboard/{Component}.tsx
   ```

4. **Update Sidebar.tsx:**
   - Remove navigation items
   - Update props (remove multi-tenant if single-user)
   - Update usage metrics

5. **Update documentation:**
   - README.md feature list
   - manifest.json features array

6. **Validate:**
   - Run integrity checks
   - Test build
   - Verify navigation

---

## 💡 Prevention Tips

1. **Start Fresh** - Build each template from minimal boilerplate, don't copy
2. **Check Feature Matrix** - Before adding ANY feature, check if it belongs
3. **Validate Early** - Run integrity checks after every major change
4. **Question Similarities** - If templates look too similar, something's wrong
5. **Document Changes** - Update feature matrix if adding new categories

---

## 🚀 Template Creation Workflow

When creating a new template:

1. ✅ Read `docs/template-integrity-checklist.md`
2. ✅ Define minimal feature set for use case
3. ✅ Build from scratch (don't copy existing template)
4. ✅ Implement only features from feature matrix
5. ✅ Run integrity validation
6. ✅ Document features in README and manifest
7. ✅ Get review before deployment

---

## 📞 When in Doubt

**Ask these questions:**

1. Does this feature match the template's primary use case?
2. Is this feature listed in the template integrity checklist?
3. Would a user of this template expect this feature?
4. Does this feature exist in another template where it makes more sense?

**If uncertain:**
- Check `docs/template-integrity-checklist.md`
- Review similar templates for patterns
- Escalate for review before implementing

---

## 🎓 Key Lessons

From the digital-download contamination fix:

1. **Contamination is subtle** - Templates share so much (auth, billing), extra features can hide
2. **Validate structure AND content** - Directory structure can be correct with wrong files inside
3. **Prevention > Cleanup** - Much easier to prevent than fix after deployment
4. **Automate checks** - Simple grep commands catch most issues
5. **Document boundaries** - Clear feature matrix prevents confusion

---

**Last Updated:** 2026-02-05  
**Version:** 1.0  
**Related Issue:** Digital-download template contamination cleanup

---

**Quick Links:**
- [Template Integrity Checklist](./template-integrity-checklist.md)
- [Contamination Fix Summary](./template-contamination-fix-summary.md)
- [Before/After Comparison](./template-cleanup-before-after.md)
