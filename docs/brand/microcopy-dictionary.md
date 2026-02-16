# Velocity Microcopy Dictionary

> Standardized UI terminology for consistent product language

---

## Naming Philosophy

Velocity's microcopy follows three principles:
1. **Clarity over Cleverness** — Users shouldn't think about what words mean
2. **Action-Oriented** — Every phrase should enable user action
3. **Consistent Patterns** — Same terms everywhere reduce cognitive load

---

## Global Terminology Standards

### Authentication

| Decision | Term | Rationale |
|----------|------|-----------|
| Entry action | **"Log in"** | Shorter, more common in B2B SaaS |
| Exit action | **"Log out"** | Consistent with entry |
| New account | **"Sign up"** | Distinct from "Log in" |
| Password recovery | **"Reset password"** | Clear, actionable |
| Remember me | **"Keep me logged in"** | Conversational, clear |

**Never use:** "Sign in" (inconsistent), "Login" (noun form), "Register" (dated)

### User References

| Decision | Term | Context |
|----------|------|---------|
| General user | **"User"** | Technical contexts, settings |
| Account holder | **"Account"** | Billing, plan contexts |
| Persona | **"Creator"** | Marketing, feature descriptions |
| Organization | **"Team"** | Multi-seat plans, collaboration |

**Never use:** "Member" (ambiguous), "Teammate" (too casual), "Customer" ( transactional)

### Destructive Actions

| Severity | Term | Use Case |
|----------|------|----------|
| Reversible | **"Remove"** | Remove from list, filter out |
| Permanent (soft) | **"Delete"** | Delete item, cannot undo |
| Permanent (hard) | **"Permanently delete"** | Data loss, requires confirmation |
| Cancel action | **"Cancel"** | Stop current process |

**Never use:** "Trash" (too casual), "Erase" (unclear scope), "Get rid of" (unprofessional)

### Navigation

| Element | Term | Notes |
|---------|------|-------|
| Main hub | **"Dashboard"** | Standard B2B term |
| Settings area | **"Settings"** | Not "Preferences" |
| User menu | **"Account"** | Profile, billing, logout |
| Help section | **"Help"** | Not "Support" (that's a contact action) |
| Documentation | **"Docs"** | Developer/API documentation |

---

## Feature-Specific Terminology

### Trends & Alerts

| Concept | Term | Alternative | Never Use |
|---------|------|-------------|-----------|
| Emerging pattern | **"Trend"** | Sound, format | Viral thing, hot content |
| Trend notification | **"Alert"** | Notification | Ping, buzz, heads up |
| Alert delivery | **"Send"** | Deliver | Fire, push |
| Alert configuration | **"Alert settings"** | Preferences | Rules, triggers |
| Rate of growth | **"Velocity"** | Growth rate | Speed, momentum |
| Category | **"Niche"** | Category | Bucket, group |
| Content type | **"Format"** | Template | Style, type |
| Audio clip | **"Sound"** | Audio | Song, track, audio clip |
| Trend example | **"Sample"** | Example | Instance, case |
| Saturation point | **"Saturation"** | Peak | Max, limit |

### Notifications

| Channel | Term | Copy Pattern |
|---------|------|--------------|
| In-app | **"Notification"** | "[Trend name] is surging in #[niche]" |
| Slack | **"Slack alert"** | "🔥 Trend Alert: [trend] +340% in #beauty" |
| Email | **"Digest"** (batch) / **"Alert"** (immediate) | "Your daily trend digest" |
| SMS | **"Text alert"** | "VELOCITY: [trend] surging +340% #beauty [link]" |

### Data & Analytics

| Concept | Term | Example |
|---------|------|---------|
| Growth percentage | **"Growth"** or **"+X%"** | "+340% growth" |
| Time period | **"Last X hours"** | "Last 24 hours" |
| All-time | **"Total"** | "Total videos: 12.4K" |
| Current value | **"Current"** | "Current velocity: +180%" |
| Data freshness | **"Updated X [time] ago"** | "Updated 5 min ago" |
| Data source | **"Tracking"** | "Tracking 2.4M videos" |

### Subscription & Billing

| Concept | Term | Notes |
|---------|------|-------|
| Payment tier | **"Plan"** | Not "Tier" or "Level" |
| Free offering | **"Free"** | Not "Basic" or "Starter" |
| Paid offering | **"Pro"**, **"Agency"**, **"Enterprise"** | Match plan names |
| Feature limit | **"Limit"** | "You've reached your alert limit" |
| Upgrade prompt | **"Upgrade"** | Not "Go premium" |
| Payment period | **"Monthly"** / **"Annual"** | Be specific |
| Invoice | **"Receipt"** | More common for SaaS |

---

## Microcopy Patterns by Context

### Buttons & CTAs

**Primary Actions (use strong verbs):**
| Context | Button Text | Rationale |
|---------|-------------|-----------|
| Create alert | **"Create Alert"** | Action + object |
| Connect Slack | **"Connect Slack"** | Clear outcome |
| Save settings | **"Save Changes"** | Explicit action |
| Start trial | **"Start Free Trial"** | Benefit + action |
| Upgrade plan | **"Upgrade to Pro"** | Destination clear |
| Generate report | **"Generate Report"** | Action + object |

**Secondary Actions:**
| Context | Button Text | Rationale |
|---------|-------------|-----------|
| Cancel action | **"Cancel"** | Standard |
| Go back | **"Back"** | Short, clear |
| Learn more | **"Learn More"** | Standard CTA |
| Skip step | **"Skip for now"** | Not permanent |

**Destructive Actions:**
| Context | Button Text | Pattern |
|---------|-------------|---------|
| Delete | **"Delete [item]"** | Action + object |
| Confirm delete | **"Yes, delete"** | Explicit confirmation |
| Cancel delete | **"No, keep it"** | Reversible action clear |
| Remove | **"Remove"** | Softer than delete |

### Empty States

| Scenario | Headline | Body | CTA |
|----------|----------|------|-----|
| No alerts yet | "No alerts configured" | "Create your first alert to start tracking trends." | "Create Alert" |
| No trends found | "No trends detected" | "Check back soon or expand your niche preferences." | "Edit Niches" |
| No notifications | "All caught up" | "You'll see new alerts here when trends emerge." | — |
| No search results | "No results found" | "Try adjusting your filters or search terms." | "Clear Filters" |
| No data (error) | "Couldn't load data" | "Refresh the page or try again in a moment." | "Try Again" |

### Form Labels & Placeholders

**Input Labels:**
| Field | Label | Placeholder |
|-------|-------|-------------|
| Email | "Email address" | "you@example.com" |
| Password | "Password" | "••••••••" |
| URL | "Slack webhook URL" | "https://hooks.slack.com/..." |
| Search | "Search trends" | "Search sounds, hashtags..." |
| Phone | "Phone number" | "+1 (555) 000-0000" |

**Helper Text:**
| Context | Helper Text |
|---------|-------------|
| Password requirements | "Must be at least 8 characters with a number and symbol." |
| Webhook setup | "Find this in your Slack app's Incoming Webhooks settings." |
| Velocity threshold | "Only alert when growth exceeds this percentage per hour." |
| Niche selection | "Select up to 5 niches on the Free plan." |

### Success Messages

| Scenario | Toast/Message |
|----------|---------------|
| Alert created | "Alert created. You'll be notified when matching trends emerge." |
| Settings saved | "Settings saved." |
| Slack connected | "Slack connected successfully." |
| Report generated | "Report ready. Download will begin automatically." |
| Password changed | "Password updated." |
| Account upgraded | "Welcome to Pro! You now have unlimited alerts." |

### Error Messages

**Pattern: "What happened. How to fix it."**

| Scenario | Error Message |
|----------|---------------|
| Network failure | "Couldn't connect to the server. Check your connection and try again." |
| Invalid credentials | "Email or password is incorrect. Try again or reset your password." |
| Slack webhook invalid | "Invalid Slack webhook URL. Check the URL and try again." |
| Rate limit | "Too many requests. Please wait a moment and try again." |
| Validation error | "Please fix the highlighted fields and try again." |
| Server error | "Something went wrong on our end. We're looking into it." |
| Payment failed | "Payment failed. Check your card details or try a different payment method." |

### Loading States

| Context | Loading Text |
|---------|--------------|
| Button loading | "Creating..." / "Saving..." / "Connecting..." |
| Page loading | "Loading trends..." |
| Data fetching | "Fetching latest data..." |
| Report generation | "Generating report..." |
| Initial load | "Starting up..." |

### Time & Dates

**Format Standards:**
| Context | Format | Example |
|---------|--------|---------|
| Timestamp (recent) | Relative | "2 min ago", "3 hours ago" |
| Timestamp (older) | Date | "Feb 16" |
| Timestamp (last year) | Full date | "Feb 16, 2025" |
| Time range | "X-Y [period]" | "Last 24 hours", "Last 7 days" |
| Duration | "X [unit]" | "2 hours", "30 minutes" |
| Future time | Relative | "In 2 hours", "Tomorrow at 3 PM" |

---

## Alert Message Templates

### Slack Alert Format

```
🔥 Trend Alert: [SOUND_NAME]

Growing +[VELOCITY]% in #[NICHE]
[PREVIOUS_COUNT] → [CURRENT_COUNT] videos in [TIME_PERIOD]
Saturation: [SATURATION_ESTIMATE]

View details: [LINK]
```

**Example:**
```
🔥 Trend Alert: soft glam transformation

Growing +340% in #beauty
847 → 2,891 videos in 3 hours
Saturation: ~18 hours until mainstream

View details: https://velocity.io/trends/123
```

### Email Digest Format

**Subject:** Your [Period] Trend Digest - [X] trends detected

**Preview:** "3 new trends in your niches: #beauty, #fitness..."

**Body Structure:**
```
Hi [NAME],

We detected [X] trending sounds in your niches this [period]:

1. [TREND_NAME] — +[VELOCITY]% in #[NICHE]
   [Brief description]
   [View Trend button]

2. [TREND_NAME] — +[VELOCITY]% in #[NICHE]
   ...

[View All Trends button]

---
Velocity Team
Unsubscribe | Update preferences
```

### SMS Alert Format

```
VELOCITY: [TREND_NAME] surging +[VELOCITY]% #[NICHE]. [LINK]
```

**Character limit:** 160 characters maximum

---

## Tone Spectrum Reference

### By Context

| Context | Tone | Example |
|---------|------|---------|
| Onboarding | Welcoming, guiding | "Welcome to Velocity. Let's set up your first alert." |
| Alert | Urgent, factual | "🔥 Trend Alert: Sound 'X' surging 340% in #beauty" |
| Success | Confident, concise | "Alert created." |
| Error | Helpful, clear | "We couldn't connect to Slack. Check your webhook URL." |
| Empty state | Encouraging | "No trends yet. Add more niches to expand coverage." |
| Upgrade prompt | Benefit-focused | "Get real-time alerts with Pro. Upgrade now." |

### Word Choice Guidelines

**Use these words:**
- Detect (not "find" or "spot")
- Alert (not "notify" or "ping")
- Configure (not "set up" for advanced features)
- Monitor (not "watch")
- Track (not "follow")
- Surging (not "going up")
- Emerging (not "new")

**Avoid these words:**
- "Just" (minimizes value)
- "Simply" (can sound condescending)
- "Obviously" (assumes knowledge)
- "Easy" (subjective, can frustrate if user struggles)
- "Bug" (use "issue" or "error")
- "Cheap" (use "affordable" or specific price)

---

## Voice Checklist

Before shipping any microcopy, verify:

- [ ] Is it direct? (No fluff)
- [ ] Is it confident? (No hedging words like "just", "maybe")
- [ ] Is it actionable? (Focuses on user action)
- [ ] Is it consistent? (Uses terms from this dictionary)
- [ ] Is it scannable? (Front-loaded, short sentences)
- [ ] Does it work out of context? (User can understand standalone)

---

*Version 1.0 | Created: 2026-02-16*
