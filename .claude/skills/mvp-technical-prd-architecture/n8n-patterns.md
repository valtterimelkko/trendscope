# n8n Workflow Patterns for MVP SaaS

## When to Use n8n

| Scenario | Use n8n | Use Edge Function |
|----------|---------|-------------------|
| Third-party API integration | ✅ | ❌ |
| User OAuth (Gmail, Drive) | ✅ (Proxy Pattern) | ❌ |
| Long-running process | ✅ | ❌ (50ms limit) |
| Webhook validation | ❌ | ✅ |
| Synchronous API response | ❌ | ✅ |

## The Logic Layer Architecture

n8n replaces traditional backend controllers for complex operations:

```
Frontend → Supabase (quick CRUD)
        → n8n webhook (complex logic)
        
Supabase → DB Webhook → n8n (async processing)
```

## Async Queue Pattern

For reliable async processing:

1. **Frontend writes job to queue table:**
```sql
INSERT INTO public.jobs (type, payload, status, organization_id)
VALUES ('generate-report', '{"date_range": "Q4"}', 'pending', org_id);
```

2. **Supabase Database Webhook triggers n8n**

3. **n8n processes and updates status:**
```sql
UPDATE public.jobs SET status = 'completed', result = '...' WHERE id = job_id;
```

4. **Frontend listens via Realtime:**
```javascript
supabase
  .channel('jobs')
  .on('postgres_changes', { event: 'UPDATE', table: 'jobs' }, handleUpdate)
  .subscribe();
```

## Multi-Tenant OAuth Proxy Pattern

**Critical:** Never store user OAuth tokens in n8n credentials. Use the Proxy Pattern.

### Architecture

```
User → Your OAuth Flow → Tokens stored in Supabase (encrypted)
                               ↓
n8n Workflow → Fetch token from Supabase → HTTP Request with Bearer token
```

### Token Storage Table

```sql
CREATE TABLE private.user_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL, -- 'google', 'microsoft', etc.
  access_token TEXT NOT NULL, -- Encrypt at rest
  refresh_token TEXT,
  expires_at TIMESTAMPTZ,
  scopes TEXT[],
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, provider)
);

-- No RLS - accessed via service role from n8n only
```

### n8n Workflow Structure

```
Webhook (receives user_id + action)
    ↓
Supabase Node: Fetch user token from private.user_tokens
    ↓
IF Node: Token expired?
    ├─ Yes → HTTP Request: Refresh token → Update Supabase
    └─ No → Continue
    ↓
HTTP Request: Call external API with Bearer token
    ↓
Supabase Node: Store result / Update status
```

### Example: Gmail Integration

```json
{
  "workflow": "send-user-email",
  "trigger": "POST /webhook/send-email",
  "nodes": [
    {
      "name": "Validate Request",
      "type": "IF",
      "check": "payload.user_id AND payload.to AND payload.body"
    },
    {
      "name": "Fetch Gmail Token",
      "type": "Supabase",
      "query": "SELECT * FROM private.user_tokens WHERE user_id = {{user_id}} AND provider = 'google'"
    },
    {
      "name": "Refresh if Expired",
      "type": "HTTP Request",
      "condition": "token.expires_at < now()",
      "url": "https://oauth2.googleapis.com/token",
      "method": "POST"
    },
    {
      "name": "Send Email",
      "type": "HTTP Request",
      "url": "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
      "headers": { "Authorization": "Bearer {{access_token}}" }
    }
  ]
}
```

## Workflow Documentation Format

Document each workflow in the PRD using this structure:

**Template:**

```
### Workflow: [Name]

**Trigger:** [Webhook URL / DB event / Schedule]

**Input Payload:**
{
  "user_id": "uuid",
  "action": "string",
  "data": {}
}

**Logic Sequence:**
1. Validate input
2. Fetch required data from Supabase
3. Call external API
4. Update result in Supabase

**Failure Modes:**
- External API timeout: Retry 3x with exponential backoff
- Invalid token: Log error, notify user via in-app message
- Supabase error: Retry once, then fail job with error details

**Success Output:**
- Job status updated to 'completed'
- Result stored in jobs.result JSONB
```

## Error Handling Patterns

### Retry with Backoff

```
Error Trigger Node
    ↓
Wait Node (delay: 2^attempt seconds, max 60s)
    ↓
Retry Counter (max 3)
    ├─ Under limit → Retry main flow
    └─ At limit → Error Handler
```

### Error Handler

```
Error Handler Node
    ↓
Supabase: Update job status = 'failed', error = details
    ↓
(Optional) Slack/Email notification to ops
```

## Webhook Security

**Always validate incoming webhooks:**

1. **Shared Secret:** Include secret in URL or header
```
/webhook/abc123?secret=YOUR_SHARED_SECRET
```

2. **Signature Validation:** For external services (Stripe, GitHub)
```javascript
// Use Edge Function for signature validation, then forward to n8n
const isValid = verifySignature(body, signature, secret);
if (!isValid) return new Response('Unauthorized', { status: 401 });
```

3. **JWT Validation:** For internal calls
```
IF Node: Check auth.jwt() is valid and not expired
```

## API Quota Management

When integrating with external APIs (Google, Microsoft, etc.), track quotas:

**Add to PRD Non-Functional Requirements:**
```markdown
### X.X API Quotas & Rate Limits

| Service | Daily Quota | Strategy |
|---------|-------------|----------|
| Google Calendar API | 1M requests/day | Batch processing, cache results |
| Gmail API | 1B units/day | Pagination, incremental sync |
| n8n webhooks (internal) | 1000/hour/user | Rate limit at Edge Function |

**Monitoring:**
- Alert when quota usage > 80%
- Exponential backoff on 429 responses
- Circuit breaker after 3 consecutive failures
```

## n8n Hosting Considerations

| Aspect | Recommendation |
|--------|----------------|
| UI Access | Behind VPN/Tailscale only |
| Webhook Endpoints | Public but secured |
| Workers | Queue mode for isolation |
| Credentials | Minimal - use Proxy Pattern |
| Backups | Export workflows to Git as JSON |

## Workflow-as-Code

Store workflows in Git:

```
n8n/
  workflows/
    onboarding-sequence.json
    report-generator.json
    email-sender.json
  README.md (workflow inventory)
```

CI/CD imports workflows via n8n API on deploy.

## Common Workflow Templates

### 1. User Onboarding
```
User Created (DB Webhook)
    → Create profile in CRM
    → Send welcome email
    → Schedule day-3 follow-up
```

### 2. Report Generation
```
Job Created (status=pending, type=report)
    → Fetch data from Supabase
    → Generate PDF
    → Upload to Storage
    → Update job with download URL
```

### 3. External Sync (Batched for Scale)
```
Schedule (every 15 min)
    → Query users needing sync (last_sync < now() - 15min)
    → Process in batches of 100
        → For each batch (parallel, max 10 concurrent):
            → Fetch updates from external API
            → Upsert into Supabase
            → Update last_sync timestamp
        → Handle rate limits: exponential backoff on 429
    → If incomplete, schedule immediate retry for remaining
```

**Scalability:** At 10,000 users, naive "for each user" hits API quota limits. Batching + concurrency control keeps you under quotas.
