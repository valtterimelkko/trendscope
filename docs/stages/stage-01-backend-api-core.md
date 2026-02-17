# Stage 01: Backend API Core

**Stage ID:** S01
**Duration Estimate:** 4-6 hours
**Complexity:** Medium
**Status:** Not Started
**Last Updated:** 2026-02-17

---

## 1. Stage Overview

### 1.1 Purpose

Complete the Backend API Core by implementing missing API endpoints that connect the frontend to the database. This stage focuses on the implementation gaps identified after Phase 4.3 template integration.

### 1.2 Objectives

1. Implement Bookmark API endpoints (CRUD for user trend bookmarks)
2. Implement Client Management API endpoints (Agency tier feature)
3. Implement Alert Management API refinements (dismiss functionality, stats endpoint)
4. Ensure all API endpoints have consistent error handling and authentication
5. Validate RLS policies work correctly with new endpoints

### 1.3 Scope

**In Scope:**
- Bookmark API endpoints: GET, POST, DELETE
- Client Management API endpoints: GET, POST, PUT, DELETE (Agency tier)
- Client Alert Configuration endpoints
- Alert dismiss endpoint
- Alert statistics endpoint

**Out of Scope:**
- Stripe webhook handlers (Stage 02)
- Scraper integration (Stage 03)
- Trend detection engine (Stage 04)
- Alert delivery pipeline (Stage 05)
- Marketing/lead capture forms (explicitly excluded per Phase 4.4)

---

## 2. Dependencies

### 2.1 Prerequisites (Already Complete from Phase 4.3)

| Dependency | Status | Location |
|------------|--------|----------|
| Database schema deployed | Complete | Supabase (11 tables with RLS) |
| Authentication configured | Complete | Supabase Auth |
| Trends API | Complete | `/api/trends`, `/api/trends/[id]` |
| User Niches API | Complete | `/api/user/niches` |
| User Integrations API | Complete | `/api/user/integrations` |
| User Profile API | Complete | `/api/user/profile` |
| Alerts API (read-only) | Complete | `/api/alerts` |

### 2.2 Required Before This Stage

- [x] Phase 4.3 Template Integration complete
- [x] Phase 4.3.5 Security Audit complete (all RLS policies verified)
- [x] Supabase project configured and accessible

### 2.3 Blocks

| Downstream Stage | Blocking Reason |
|------------------|-----------------|
| Stage 02: Stripe Webhooks | Requires profile API for tier validation |
| Stage 05: Alert Pipeline | Requires bookmark API for engagement tracking |

---

## 3. Technical Components

### 3.1 Files to Create

```
frontend/app/api/bookmarks/route.ts          # Bookmark list & create
frontend/app/api/bookmarks/[id]/route.ts     # Bookmark delete & update
frontend/app/api/clients/route.ts            # Client list & create (Agency)
frontend/app/api/clients/[id]/route.ts       # Client CRUD (Agency)
frontend/app/api/clients/[id]/alerts/route.ts # Client alert configs
frontend/app/api/alerts/[id]/dismiss/route.ts # Dismiss alert
frontend/app/api/alerts/stats/route.ts       # Alert statistics
```

### 3.2 Files to Modify

```
frontend/app/api/alerts/route.ts             # Add support for dismissed filter
```

### 3.3 Shared Components Used

- `createClient()` from `@/lib/supabase/server` - Server-side Supabase client with RLS
- Next.js 15 App Router conventions
- Standardized error response format

---

## 4. API Contracts

### 4.1 Bookmark Endpoints

#### GET /api/bookmarks

**Description:** List user's bookmarked trends

**Authentication:** Required (Supabase Auth)

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | integer | No | 50 | Max items per page (max 100) |
| offset | integer | No | 0 | Pagination offset |

**Response (200):**
```json
{
  "bookmarks": [
    {
      "id": "uuid",
      "trend_id": "uuid",
      "notes": "string | null",
      "created_at": "ISO8601",
      "trend": {
        "id": "uuid",
        "name": "string",
        "type": "sound | hashtag | format",
        "velocity_score": 0-100,
        "saturation_percent": 0-100,
        "status": "emerging | peaking | saturated | expired"
      }
    }
  ],
  "total": 0
}
```

**Error Responses:**
- `401 Unauthorized` - User not authenticated
- `500 Internal Server Error` - Database error

---

#### POST /api/bookmarks

**Description:** Bookmark a trend

**Authentication:** Required (Supabase Auth)

**Request Body:**
```json
{
  "trend_id": "uuid (required)",
  "notes": "string (optional, max 500 chars)"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "trend_id": "uuid",
  "notes": "string | null",
  "created_at": "ISO8601"
}
```

**Error Responses:**
- `400 Bad Request` - Missing trend_id
- `404 Not Found` - Trend not found
- `409 Conflict` - Trend already bookmarked
- `401 Unauthorized` - User not authenticated

---

#### DELETE /api/bookmarks/[id]

**Description:** Remove a bookmark

**Authentication:** Required (Supabase Auth)

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | uuid | Yes | Bookmark ID |

**Response (204):** No content

**Error Responses:**
- `404 Not Found` - Bookmark not found or not owned by user
- `401 Unauthorized` - User not authenticated

---

#### PATCH /api/bookmarks/[id]

**Description:** Update bookmark notes

**Authentication:** Required (Supabase Auth)

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | uuid | Yes | Bookmark ID |

**Request Body:**
```json
{
  "notes": "string (optional, max 500 chars)"
}
```

**Response (200):**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "trend_id": "uuid",
  "notes": "string | null",
  "created_at": "ISO8601"
}
```

**Error Responses:**
- `400 Bad Request` - No fields to update
- `404 Not Found` - Bookmark not found
- `401 Unauthorized` - User not authenticated

---

### 4.2 Client Management Endpoints (Agency Tier)

#### GET /api/clients

**Description:** List agency's client workspaces

**Authentication:** Required (Agency tier or higher)

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | integer | No | 50 | Max items per page |
| offset | integer | No | 0 | Pagination offset |
| is_active | boolean | No | - | Filter by active status |

**Response (200):**
```json
{
  "clients": [
    {
      "id": "uuid",
      "name": "string",
      "logo_url": "string | null",
      "config": {
        "niches": ["uuid"],
        "alert_preferences": {}
      },
      "is_active": true,
      "created_at": "ISO8601",
      "updated_at": "ISO8601"
    }
  ],
  "total": 0,
  "max_allowed": 5
}
```

**Tier Limits:**
| Tier | Max Clients |
|------|-------------|
| free | 0 |
| solo | 0 |
| agency | 5 |
| enterprise | 20 |

**Error Responses:**
- `401 Unauthorized` - User not authenticated
- `403 Forbidden` - User tier does not support client management
- `500 Internal Server Error` - Database error

---

#### POST /api/clients

**Description:** Create a client workspace

**Authentication:** Required (Agency tier or higher)

**Request Body:**
```json
{
  "name": "string (required, max 100 chars)",
  "logo_url": "string (optional, valid URL)",
  "config": {
    "niches": ["uuid"],
    "alert_preferences": {
      "velocity_threshold": 50,
      "channels": ["slack", "email"]
    }
  }
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "agency_id": "uuid",
  "name": "string",
  "logo_url": "string | null",
  "config": {},
  "is_active": true,
  "created_at": "ISO8601"
}
```

**Error Responses:**
- `400 Bad Request` - Missing name or invalid data
- `403 Forbidden` - Max clients reached for tier
- `401 Unauthorized` - User not authenticated

---

#### GET /api/clients/[id]

**Description:** Get client workspace details

**Authentication:** Required (Agency tier, owner of client)

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | uuid | Yes | Client ID |

**Response (200):**
```json
{
  "id": "uuid",
  "agency_id": "uuid",
  "name": "string",
  "logo_url": "string | null",
  "config": {
    "niches": ["uuid"],
    "alert_preferences": {}
  },
  "is_active": true,
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "alert_integrations": [
    {
      "id": "uuid",
      "type": "slack | webhook | discord",
      "name": "string",
      "is_active": true
    }
  ],
  "recent_trends": [
    {
      "id": "uuid",
      "name": "string",
      "velocity_score": 0-100
    }
  ]
}
```

**Error Responses:**
- `404 Not Found` - Client not found or not owned by agency
- `401 Unauthorized` - User not authenticated

---

#### PUT /api/clients/[id]

**Description:** Update client workspace

**Authentication:** Required (Agency tier, owner of client)

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | uuid | Yes | Client ID |

**Request Body:**
```json
{
  "name": "string (optional)",
  "logo_url": "string (optional)",
  "config": {} (optional),
  "is_active": "boolean (optional)"
}
```

**Response (200):** Updated client object

**Error Responses:**
- `400 Bad Request` - No fields to update
- `404 Not Found` - Client not found
- `401 Unauthorized` - User not authenticated

---

#### DELETE /api/clients/[id]

**Description:** Delete client workspace (cascades to client_alerts)

**Authentication:** Required (Agency tier, owner of client)

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | uuid | Yes | Client ID |

**Response (204):** No content

**Error Responses:**
- `404 Not Found` - Client not found
- `401 Unauthorized` - User not authenticated

---

### 4.3 Alert Management Refinements

#### PATCH /api/alerts/[id]/dismiss

**Description:** Dismiss an alert (mark as dismissed)

**Authentication:** Required (Owner of alert)

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | uuid | Yes | Alert ID |

**Response (200):**
```json
{
  "id": "uuid",
  "dismissed": true
}
```

**Error Responses:**
- `404 Not Found` - Alert not found
- `401 Unauthorized` - User not authenticated

---

#### GET /api/alerts/stats

**Description:** Get alert statistics for the current user

**Authentication:** Required (Supabase Auth)

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| period | string | No | week | Period: 'week' or 'month' |

**Response (200):**
```json
{
  "total_this_week": 15,
  "total_this_month": 47,
  "by_niche": [
    {
      "niche_id": "uuid",
      "niche_name": "string",
      "count": 10
    }
  ],
  "by_status": {
    "pending": 5,
    "sent": 8,
    "delivered": 10,
    "failed": 2
  },
  "action_rate": 0.45,
  "bookmark_rate": 0.23
}
```

**Error Responses:**
- `401 Unauthorized` - User not authenticated

---

## 5. Database Schema Changes

### 5.1 No Schema Changes Required

All required tables already exist from Phase 4.3:

- `bookmarks` - Ready for use
- `clients` - Ready for use
- `client_alerts` - Ready for use
- `alerts` - Already has `dismissed` column

### 5.2 RLS Policy Verification

All tables have RLS enabled with appropriate policies:

| Table | RLS Status | Policy |
|-------|------------|--------|
| bookmarks | Enabled | Users can manage own bookmarks |
| clients | Enabled | Agencies can manage own clients |
| client_alerts | Enabled | Agencies can view own client alerts |
| alerts | Enabled | Users can view own alerts |

---

## 6. Testing Requirements

### 6.1 Unit Tests

- [ ] Bookmark CRUD operations
- [ ] Client CRUD operations with tier enforcement
- [ ] Alert dismiss functionality
- [ ] Alert statistics calculations

### 6.2 Integration Tests

- [ ] Full bookmark flow: create, list, update, delete
- [ ] Client management flow with tier limits
- [ ] RLS policy enforcement (cross-user access blocked)
- [ ] Authentication required on all endpoints

### 6.3 Manual Testing Checklist

- [ ] Create bookmark via API
- [ ] List bookmarks with pagination
- [ ] Update bookmark notes
- [ ] Delete bookmark
- [ ] Create client (Agency tier user)
- [ ] Client creation blocked for non-Agency users
- [ ] Max client limit enforced
- [ ] Dismiss alert
- [ ] View alert statistics

---

## 7. Security Considerations

### 7.1 Authentication

- All endpoints require Supabase Auth JWT validation
- Use `createClient()` from server.ts for RLS enforcement

### 7.2 Authorization

- Client endpoints require Agency tier or higher
- RLS policies enforce data isolation
- Tier limits enforced server-side (never trust client)

### 7.3 Input Validation

- Validate UUID formats for all ID parameters
- Enforce max lengths on text fields (notes: 500, name: 100)
- Validate JSONB config structure for clients

### 7.4 Sensitive Data

- Never expose other users' data
- Mask webhook URLs in responses (already done in integrations)
- Don't leak tier information across users

---

## 8. Performance Considerations

### 8.1 Database Queries

- Use Supabase query builder with proper indexing
- Use `.range()` for pagination (don't fetch all then slice)
- Use `.select()` with specific columns (avoid SELECT *)

### 8.2 Caching

- Consider caching user tier lookups (frequent checks)
- No heavy caching needed for MVP (low traffic expected)

### 8.3 Rate Limiting

- Inherit Next.js default limits
- Consider adding per-user rate limits post-MVP

---

## 9. Implementation Notes

### 9.1 Code Patterns to Follow

Based on existing Phase 4.3 implementations:

```typescript
// Standard error handling pattern
export async function GET(request: NextRequest) {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // ... business logic

    return NextResponse.json(data);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
```

### 9.2 Tier Check Pattern

```typescript
const tierLimits: Record<string, number> = {
  free: 0,
  solo: 0,
  agency: 5,
  enterprise: 20
};

const { data: profile } = await supabase
  .from('profiles')
  .select('tier')
  .eq('id', user.id)
  .single();

const maxAllowed = tierLimits[profile?.tier || 'free'] || 0;

if (maxAllowed === 0) {
  return NextResponse.json({
    error: 'Client management requires Agency tier or higher'
  }, { status: 403 });
}
```

---

## 10. Progress Log

| Date | Task | Status | Notes |
|------|------|--------|-------|
| 2026-02-17 | Architecture plan created | Complete | This document |
| 2026-02-17 | Bookmarks API (GET/POST) | Complete | /api/bookmarks/route.ts |
| 2026-02-17 | Bookmark by ID API (PATCH/DELETE) | Complete | /api/bookmarks/[id]/route.ts |
| 2026-02-17 | Clients API (GET/POST) | Complete | /api/clients/route.ts with tier enforcement |
| 2026-02-17 | Client by ID API (GET/PUT/DELETE) | Complete | /api/clients/[id]/route.ts |
| 2026-02-17 | Alert stats API (GET) | Complete | /api/alerts/stats/route.ts |
| 2026-02-17 | Alert dismiss API (PATCH) | Complete | /api/alerts/[id]/dismiss/route.ts |
| 2026-02-17 | Alerts route updated | Complete | Added dismissed filter support |

---

## 11. Issues Log

| ID | Description | Status | Resolution |
|----|-------------|--------|------------|
| - | - | - | - |

---

## 12. Completion Checklist

- [x] All Bookmark API endpoints implemented
- [x] All Client Management API endpoints implemented
- [x] Alert dismiss endpoint implemented
- [x] Alert stats endpoint implemented
- [x] All endpoints have authentication
- [x] RLS policies verified (uses existing RLS from Phase 4.3.5)
- [ ] Unit tests passing (deferred to integration testing)
- [ ] Manual testing complete
- [ ] Code reviewed
- [ ] Merged to main

---

## 13. References

- Technical PRD: `docs/Project-Technical-Architecture.md`
- Security Audit: `docs/supabase-security-audit.md`
- Progress Tracker: `PROGRESS.md`
- Existing API Routes: `frontend/app/api/`

---

*Stage Architecture Plan - Generated by Stage Architect Agent*
*Phase 4.4 - Stage Architecture Planning*
