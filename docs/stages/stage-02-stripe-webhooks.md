# Stage 02: Stripe Webhook Handlers

**Status:** Planned
**Estimated Duration:** 4-6 hours
**Assigned Agent:** Unassigned
**Last Updated:** 2026-02-17

---

## 1. Overview

This stage implements the Stripe webhook endpoint and billing service layer that handles subscription lifecycle events. When users upgrade, downgrade, or cancel their subscriptions via Stripe Checkout, these webhooks synchronize the payment state with the Trendscope database, updating user tiers and subscription status.

**Delivers:**
- Stripe webhook endpoint at `/api/webhooks/stripe` with signature verification
- Billing service layer for subscription management
- Tier-based feature gate utilities
- Grace period handling for failed payments
- Subscription status synchronization logic

**Success Criteria:**
- [ ] Stripe webhook signature verification passes for all incoming events
- [ ] `checkout.session.completed` activates subscription and updates tier
- [ ] `invoice.paid` confirms payment and ensures correct tier
- [ ] `invoice.payment_failed` triggers grace period logic
- [ ] `customer.subscription.updated` handles tier upgrades/downgrades
- [ ] `customer.subscription.deleted` handles cancellation correctly
- [ ] Users gain immediate access to paid features after checkout
- [ ] Webhook endpoint returns 200 within 10 seconds (Stripe requirement)

---

## 2. Dependencies

### Must Complete First
| Stage | Status | What We Need |
|-------|--------|--------------|
| Stage 01: Backend API Core | Required (Planned) | Database service layer, Supabase client setup, profiles table access pattern |

### External Dependencies
| Dependency | Status | What We Need |
|------------|--------|--------------|
| Stripe Products/Prices | Needed | STRIPE_PRICE_SOLO, STRIPE_PRICE_AGENCY, STRIPE_PRICE_ENTERPRISE environment variables |
| Stripe Webhook Secret | Needed | STRIPE_WEBHOOK_SECRET for signature verification |
| Supabase Service Role | Available | SUPABASE_SERVICE_ROLE_KEY for server-side database operations |

### Can Run In Parallel
- Stage 03: Scraper Integration - no conflicts (different subsystem)
- Stage 04: Trend Detection Engine - no conflicts (different subsystem)

### Blocks These Stages
- Stage 05: Alert Pipeline - depends on tier-based latency routing (needs feature gates)

---

## 3. Technical Components

### 3.1 Stripe Webhook Endpoint

**File:** `/frontend/app/api/webhooks/stripe/route.ts`

The webhook endpoint receives POST requests from Stripe, verifies the signature, and routes events to appropriate handlers.

```typescript
// /frontend/app/api/webhooks/stripe/route.ts

import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { handleCheckoutComplete } from '@/lib/billing/handlers/checkout-complete';
import { handleInvoicePaid } from '@/lib/billing/handlers/invoice-paid';
import { handleInvoiceFailed } from '@/lib/billing/handlers/invoice-failed';
import { handleSubscriptionUpdated } from '@/lib/billing/handlers/subscription-updated';
import { handleSubscriptionDeleted } from '@/lib/billing/handlers/subscription-deleted';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
});

const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

// Event type to handler mapping
const eventHandlers: Record<string, (event: Stripe.Event) => Promise<void>> = {
  'checkout.session.completed': handleCheckoutComplete,
  'invoice.paid': handleInvoicePaid,
  'invoice.payment_failed': handleInvoiceFailed,
  'customer.subscription.updated': handleSubscriptionUpdated,
  'customer.subscription.deleted': handleSubscriptionDeleted,
};

export async function POST(request: NextRequest) {
  const body = await request.text();
  const signature = request.headers.get('stripe-signature');

  if (!signature) {
    console.error('[Stripe Webhook] Missing stripe-signature header');
    return NextResponse.json(
      { error: 'Missing signature' },
      { status: 400 }
    );
  }

  let event: Stripe.Event;

  try {
    // Verify webhook signature - CRITICAL for security
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    console.error('[Stripe Webhook] Signature verification failed:', errorMessage);
    return NextResponse.json(
      { error: 'Invalid signature' },
      { status: 400 }
    );
  }

  // Get handler for this event type
  const handler = eventHandlers[event.type];

  if (!handler) {
    // Log unhandled events but don't fail - Stripe expects 200
    console.log(`[Stripe Webhook] Unhandled event type: ${event.type}`);
    return NextResponse.json({ received: true, handled: false });
  }

  try {
    // Process the event
    await handler(event);
    console.log(`[Stripe Webhook] Successfully processed: ${event.type}`);
    return NextResponse.json({ received: true, handled: true });
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    console.error(`[Stripe Webhook] Error processing ${event.type}:`, errorMessage);

    // Return 200 to acknowledge receipt but log error
    // Stripe will retry if we return 5xx, but we don't want retries for business logic errors
    return NextResponse.json({
      received: true,
      handled: false,
      error: errorMessage
    });
  }
}
```

### 3.2 Billing Service Layer

**File:** `/frontend/lib/billing/subscription-service.ts`

Core service for subscription operations with Supabase.

```typescript
// /frontend/lib/billing/subscription-service.ts

import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY! // Service role for webhook operations
);

// Tier mapping from Stripe price IDs
const PRICE_TO_TIER: Record<string, string> = {
  [process.env.STRIPE_PRICE_SOLO!]: 'solo',
  [process.env.STRIPE_PRICE_AGENCY!]: 'agency',
  [process.env.STRIPE_PRICE_ENTERPRISE!]: 'enterprise',
};

export interface SubscriptionUpdate {
  stripeCustomerId: string;
  stripeSubscriptionId: string | null;
  tier: 'free' | 'solo' | 'agency' | 'enterprise';
  status: 'active' | 'paused' | 'cancelled';
}

export class SubscriptionService {
  /**
   * Update user subscription based on Stripe data
   */
  static async updateSubscription(
    stripeCustomerId: string,
    data: Partial<SubscriptionUpdate>
  ): Promise<{ success: boolean; userId?: string; error?: string }> {
    // Find user by stripe_customer_id
    const { data: profile, error: findError } = await supabase
      .from('profiles')
      .select('id, tier, status')
      .eq('stripe_customer_id', stripeCustomerId)
      .single();

    if (findError || !profile) {
      console.error('[SubscriptionService] User not found for customer:', stripeCustomerId);
      return { success: false, error: 'User not found' };
    }

    // Update profile with new subscription data
    const { error: updateError } = await supabase
      .from('profiles')
      .update({
        tier: data.tier || profile.tier,
        status: data.status || profile.status,
        stripe_subscription_id: data.stripeSubscriptionId,
        updated_at: new Date().toISOString(),
      })
      .eq('id', profile.id);

    if (updateError) {
      console.error('[SubscriptionService] Failed to update profile:', updateError);
      return { success: false, error: updateError.message };
    }

    console.log(`[SubscriptionService] Updated user ${profile.id}: tier=${data.tier}, status=${data.status}`);
    return { success: true, userId: profile.id };
  }

  /**
   * Get tier from Stripe price ID
   */
  static getTierFromPrice(priceId: string): string {
    return PRICE_TO_TIER[priceId] || 'free';
  }

  /**
   * Create Stripe customer for user if not exists
   */
  static async ensureStripeCustomer(
    userId: string,
    email: string
  ): Promise<{ stripeCustomerId: string } | { error: string }> {
    const { data: profile } = await supabase
      .from('profiles')
      .select('stripe_customer_id')
      .eq('id', userId)
      .single();

    if (profile?.stripe_customer_id) {
      return { stripeCustomerId: profile.stripe_customer_id };
    }

    // Create new Stripe customer
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
    const customer = await stripe.customers.create({
      email,
      metadata: { userId },
    });

    // Update profile with customer ID
    await supabase
      .from('profiles')
      .update({ stripe_customer_id: customer.id })
      .eq('id', userId);

    return { stripeCustomerId: customer.id };
  }
}
```

### 3.3 Webhook Event Handlers

#### Handler: checkout.session.completed

**File:** `/frontend/lib/billing/handlers/checkout-complete.ts`

```typescript
// /frontend/lib/billing/handlers/checkout-complete.ts

import Stripe from 'stripe';
import { SubscriptionService } from '../subscription-service';

/**
 * Handle checkout.session.completed event
 * Fires when user completes Stripe Checkout
 */
export async function handleCheckoutComplete(event: Stripe.Event): Promise<void> {
  const session = event.data.object as Stripe.Checkout.Session;

  const stripeCustomerId = session.customer as string;
  const stripeSubscriptionId = session.subscription as string;
  const priceId = session.metadata?.priceId || session.line_items?.data[0]?.price?.id;

  if (!stripeCustomerId) {
    throw new Error('No customer ID in checkout session');
  }

  // Determine tier from price
  const tier = priceId
    ? SubscriptionService.getTierFromPrice(priceId)
    : 'solo'; // Default to solo if price not found

  // Update user subscription
  const result = await SubscriptionService.updateSubscription(stripeCustomerId, {
    stripeCustomerId,
    stripeSubscriptionId,
    tier: tier as any,
    status: 'active',
  });

  if (!result.success) {
    throw new Error(`Failed to update subscription: ${result.error}`);
  }

  console.log(`[handleCheckoutComplete] User ${result.userId} upgraded to ${tier}`);
}
```

#### Handler: invoice.paid

**File:** `/frontend/lib/billing/handlers/invoice-paid.ts`

```typescript
// /frontend/lib/billing/handlers/invoice-paid.ts

import Stripe from 'stripe';
import { SubscriptionService } from '../subscription-service';

/**
 * Handle invoice.paid event
 * Fires when a subscription payment succeeds (renewals)
 */
export async function handleInvoicePaid(event: Stripe.Event): Promise<void> {
  const invoice = event.data.object as Stripe.Invoice;

  const stripeCustomerId = invoice.customer as string;
  const stripeSubscriptionId = invoice.subscription as string;

  // Get subscription details to determine tier
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
  const subscription = await stripe.subscriptions.retrieve(stripeSubscriptionId);
  const priceId = subscription.items.data[0]?.price?.id;

  const tier = priceId
    ? SubscriptionService.getTierFromPrice(priceId)
    : 'solo';

  // Ensure subscription is active
  const result = await SubscriptionService.updateSubscription(stripeCustomerId, {
    stripeCustomerId,
    stripeSubscriptionId,
    tier: tier as any,
    status: 'active',
  });

  if (!result.success) {
    throw new Error(`Failed to confirm subscription: ${result.error}`);
  }

  console.log(`[handleInvoicePaid] Subscription confirmed for user ${result.userId}, tier=${tier}`);
}
```

#### Handler: invoice.payment_failed

**File:** `/frontend/lib/billing/handlers/invoice-failed.ts`

```typescript
// /frontend/lib/billing/handlers/invoice-failed.ts

import Stripe from 'stripe';
import { SubscriptionService } from '../subscription-service';

/**
 * Handle invoice.payment_failed event
 * Fires when a subscription payment fails
 *
 * Grace Period Logic:
 * - First failure: Log warning, keep access (will retry)
 * - After final attempt: Downgrade to free tier
 */
export async function handleInvoiceFailed(event: Stripe.Event): Promise<void> {
  const invoice = event.data.object as Stripe.Invoice;

  const stripeCustomerId = invoice.customer as string;
  const attemptCount = invoice.attempt_count || 1;

  console.warn(`[handleInvoiceFailed] Payment failed for customer ${stripeCustomerId}, attempt ${attemptCount}`);

  // Check if this is the final attempt (Stripe typically retries 3-4 times)
  const isFinalAttempt = attemptCount >= 4;

  if (isFinalAttempt) {
    // Downgrade to free tier after final failed attempt
    const result = await SubscriptionService.updateSubscription(stripeCustomerId, {
      stripeCustomerId,
      stripeSubscriptionId: null,
      tier: 'free',
      status: 'paused',
    });

    if (!result.success) {
      throw new Error(`Failed to handle payment failure: ${result.error}`);
    }

    console.log(`[handleInvoiceFailed] User ${result.userId} downgraded to free after payment failure`);

    // TODO: Send email notification about payment failure
  } else {
    // Not final attempt - just log, Stripe will retry
    console.log(`[handleInvoiceFailed] Payment will be retried by Stripe`);
  }
}
```

#### Handler: customer.subscription.updated

**File:** `/frontend/lib/billing/handlers/subscription-updated.ts`

```typescript
// /frontend/lib/billing/handlers/subscription-updated.ts

import Stripe from 'stripe';
import { SubscriptionService } from '../subscription-service';

/**
 * Handle customer.subscription.updated event
 * Fires when subscription is upgraded/downgraded or status changes
 */
export async function handleSubscriptionUpdated(event: Stripe.Event): Promise<void> {
  const subscription = event.data.object as Stripe.Subscription;

  const stripeCustomerId = subscription.customer as string;
  const priceId = subscription.items.data[0]?.price?.id;

  // Map Stripe subscription status to our status
  const statusMap: Record<string, 'active' | 'paused' | 'cancelled'> = {
    'active': 'active',
    'trialing': 'active',
    'past_due': 'paused',
    'unpaid': 'paused',
    'canceled': 'cancelled',
    'incomplete': 'paused',
    'incomplete_expired': 'cancelled',
  };

  const status = statusMap[subscription.status] || 'paused';
  const tier = priceId
    ? SubscriptionService.getTierFromPrice(priceId)
    : 'free';

  const result = await SubscriptionService.updateSubscription(stripeCustomerId, {
    stripeCustomerId,
    stripeSubscriptionId: subscription.id,
    tier: tier as any,
    status,
  });

  if (!result.success) {
    throw new Error(`Failed to update subscription: ${result.error}`);
  }

  console.log(`[handleSubscriptionUpdated] User ${result.userId} subscription updated: tier=${tier}, status=${status}`);
}
```

#### Handler: customer.subscription.deleted

**File:** `/frontend/lib/billing/handlers/subscription-deleted.ts`

```typescript
// /frontend/lib/billing/handlers/subscription-deleted.ts

import Stripe from 'stripe';
import { SubscriptionService } from '../subscription-service';

/**
 * Handle customer.subscription.deleted event
 * Fires when subscription is cancelled (end of billing period or immediately)
 */
export async function handleSubscriptionDeleted(event: Stripe.Event): Promise<void> {
  const subscription = event.data.object as Stripe.Subscription;

  const stripeCustomerId = subscription.customer as string;

  // Downgrade to free tier
  const result = await SubscriptionService.updateSubscription(stripeCustomerId, {
    stripeCustomerId,
    stripeSubscriptionId: null,
    tier: 'free',
    status: 'cancelled',
  });

  if (!result.success) {
    throw new Error(`Failed to handle cancellation: ${result.error}`);
  }

  console.log(`[handleSubscriptionDeleted] User ${result.userId} subscription cancelled, downgraded to free`);

  // TODO: Send cancellation confirmation email
}
```

### 3.4 Tier-Based Feature Gates

**File:** `/frontend/lib/billing/feature-gates.ts`

```typescript
// /frontend/lib/billing/feature-gates.ts

/**
 * Tier limits and feature access configuration
 */
export const TIER_LIMITS = {
  free: {
    niches: 1,
    alertLatency: 24 * 60 * 60 * 1000, // 24 hours (daily digest)
    maxAlerts: 10,
    velocityThreshold: 70, // Only high-confidence alerts
    hasSlackIntegration: false,
    hasEmailDigest: true,
    hasAgencyFeatures: false,
    maxClients: 0,
  },
  solo: {
    niches: 5,
    alertLatency: 2 * 60 * 60 * 1000, // 2 hours
    maxAlerts: 100,
    velocityThreshold: 50,
    hasSlackIntegration: true,
    hasEmailDigest: true,
    hasAgencyFeatures: false,
    maxClients: 0,
  },
  agency: {
    niches: 10,
    alertLatency: 30 * 60 * 1000, // 30 minutes
    maxAlerts: 1000,
    velocityThreshold: 30,
    hasSlackIntegration: true,
    hasEmailDigest: true,
    hasAgencyFeatures: true,
    maxClients: 5,
  },
  enterprise: {
    niches: 20,
    alertLatency: 0, // Real-time
    maxAlerts: Infinity,
    velocityThreshold: 0, // All alerts
    hasSlackIntegration: true,
    hasEmailDigest: true,
    hasAgencyFeatures: true,
    maxClients: 20,
  },
} as const;

export type Tier = keyof typeof TIER_LIMITS;

/**
 * Check if user can add more niches
 */
export function canAddNiche(currentTier: Tier, currentCount: number): boolean {
  return currentCount < TIER_LIMITS[currentTier].niches;
}

/**
 * Check if user can access Slack integration
 */
export function canUseSlackIntegration(currentTier: Tier): boolean {
  return TIER_LIMITS[currentTier].hasSlackIntegration;
}

/**
 * Check if user can access agency features
 */
export function canUseAgencyFeatures(currentTier: Tier): boolean {
  return TIER_LIMITS[currentTier].hasAgencyFeatures;
}

/**
 * Check if user can add more clients
 */
export function canAddClient(currentTier: Tier, currentCount: number): boolean {
  return currentCount < TIER_LIMITS[currentTier].maxClients;
}

/**
 * Get alert latency for tier
 */
export function getAlertLatency(tier: Tier): number {
  return TIER_LIMITS[tier].alertLatency;
}

/**
 * Check if alert should be sent based on velocity threshold
 */
export function shouldSendAlert(tier: Tier, velocityScore: number): boolean {
  return velocityScore >= TIER_LIMITS[tier].velocityThreshold;
}

/**
 * React hook for feature gates (client-side)
 */
export function useFeatureGates(tier: Tier) {
  return {
    limits: TIER_LIMITS[tier],
    canAddNiche: (count: number) => canAddNiche(tier, count),
    canUseSlack: () => canUseSlackIntegration(tier),
    canUseAgency: () => canUseAgencyFeatures(tier),
    canAddClient: (count: number) => canAddClient(tier, count),
    alertLatency: getAlertLatency(tier),
  };
}
```

### 3.5 Checkout Session Creation

**File:** `/frontend/app/api/checkout/route.ts`

```typescript
// /frontend/app/api/checkout/route.ts

import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { createClient } from '@/lib/supabase/server';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
});

const PRICE_MAP = {
  solo: process.env.STRIPE_PRICE_SOLO!,
  agency: process.env.STRIPE_PRICE_AGENCY!,
  enterprise: process.env.STRIPE_PRICE_ENTERPRISE!,
};

export async function POST(request: NextRequest) {
  try {
    const { tier } = await request.json();

    if (!tier || !PRICE_MAP[tier as keyof typeof PRICE_MAP]) {
      return NextResponse.json(
        { error: 'Invalid tier' },
        { status: 400 }
      );
    }

    // Get authenticated user
    const supabase = await createClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Get user profile
    const { data: profile } = await supabase
      .from('profiles')
      .select('stripe_customer_id')
      .eq('id', user.id)
      .single();

    let customerId = profile?.stripe_customer_id;

    // Create Stripe customer if not exists
    if (!customerId) {
      const customer = await stripe.customers.create({
        email: user.email,
        metadata: { userId: user.id },
      });
      customerId = customer.id;

      // Update profile with customer ID
      await supabase
        .from('profiles')
        .update({ stripe_customer_id: customerId })
        .eq('id', user.id);
    }

    // Create checkout session
    const session = await stripe.checkout.sessions.create({
      customer: customerId,
      mode: 'subscription',
      payment_method_types: ['card'],
      line_items: [
        {
          price: PRICE_MAP[tier as keyof typeof PRICE_MAP],
          quantity: 1,
        },
      ],
      success_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?checkout=success`,
      cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/pricing?checkout=canceled`,
      metadata: {
        userId: user.id,
        tier,
      },
    });

    return NextResponse.json({ sessionId: session.id, url: session.url });
  } catch (error) {
    console.error('[Checkout] Error:', error);
    return NextResponse.json(
      { error: 'Failed to create checkout session' },
      { status: 500 }
    );
  }
}
```

---

## 4. API Contracts

### Endpoints Created

#### POST /api/webhooks/stripe

**Purpose:** Receive and process Stripe webhook events

**Request:**
- Headers:
  - `Stripe-Signature`: string (required) - HMAC signature from Stripe
  - `Content-Type`: application/json
- Body: Stripe Event object

**Response (200):**
```json
{
  "received": true,
  "handled": true
}
```

**Response (400 - Invalid Signature):**
```json
{
  "error": "Invalid signature"
}
```

**Notes:**
- Must respond within 10 seconds
- Returns 200 even for unhandled events (Stripe requirement)
- Logs unhandled event types for monitoring

#### POST /api/checkout

**Purpose:** Create Stripe Checkout session for subscription upgrade

**Request:**
```json
{
  "tier": "solo" | "agency" | "enterprise"
}
```

**Response (200):**
```json
{
  "sessionId": "cs_test_xxx",
  "url": "https://checkout.stripe.com/c/pay/xxx"
}
```

**Response (401):**
```json
{
  "error": "Unauthorized"
}
```

**Response (400):**
```json
{
  "error": "Invalid tier"
}
```

### Endpoints Consumed

| Endpoint | Purpose | Stage That Creates It |
|----------|---------|----------------------|
| Supabase profiles table | User data & subscription state | Phase 4.3 (Template) |
| Supabase auth | User authentication | Phase 4.3 (Template) |

---

## 5. Database Schema Changes

### Tables Modified

| Table | Change | Migration |
|-------|--------|-----------|
| `profiles` | Updated via service layer (no schema changes) | N/A - uses existing columns |

### Existing Columns Used

The `profiles` table already has the required columns:
- `stripe_customer_id` (TEXT) - Stripe customer ID
- `stripe_subscription_id` (TEXT) - Stripe subscription ID
- `tier` (TEXT) - User tier: 'free' | 'solo' | 'agency' | 'enterprise'
- `status` (TEXT) - Subscription status: 'active' | 'paused' | 'cancelled'
- `updated_at` (TIMESTAMPTZ) - Last update timestamp

### No New Indexes Required

Existing indexes are sufficient:
- `idx_profiles_stripe_customer` on `stripe_customer_id`

---

## 6. Testing Requirements

### Unit Tests

| Test | What It Validates |
|------|------------------|
| `test_signature_verification_valid` | Valid Stripe signature passes verification |
| `test_signature_verification_invalid` | Invalid signature returns 400 |
| `test_signature_verification_missing` | Missing signature returns 400 |
| `test_get_tier_from_price` | Price ID correctly maps to tier |
| `test_tier_limits_free` | Free tier limits are enforced |
| `test_tier_limits_solo` | Solo tier limits are enforced |
| `test_tier_limits_agency` | Agency tier limits are enforced |
| `test_can_add_niche` | Niche limit check works correctly |
| `test_can_add_client` | Client limit check works correctly |

### Integration Tests

| Test | What It Validates |
|------|------------------|
| `test_checkout_complete_flow` | Full checkout.session.completed flow updates user |
| `test_invoice_paid_flow` | Invoice payment updates subscription |
| `test_invoice_failed_grace_period` | Payment failure triggers grace period |
| `test_subscription_update_flow` | Subscription update changes tier |
| `test_subscription_delete_flow` | Cancellation downgrades to free |

### Manual Verification

- [ ] Stripe CLI forwards webhooks to local development
- [ ] Checkout session creates and redirects correctly
- [ ] User tier updates immediately after checkout completion
- [ ] Failed payment logs warning and eventually downgrades
- [ ] Cancellation sets status to 'cancelled' and tier to 'free'

### Testing Webhooks Locally

1. Install Stripe CLI:
   ```bash
   # macOS
   brew install stripe/stripe-cli/stripe

   # Linux
   wget https://github.com/stripe/stripe-cli/releases/download/v1.19.4/stripe_1.19.4_linux_x86_64.tar.gz
   tar -xvf stripe_1.19.4_linux_x86_64.tar.gz
   sudo mv stripe /usr/local/bin/
   ```

2. Login to Stripe:
   ```bash
   stripe login
   ```

3. Forward webhooks to local dev server:
   ```bash
   stripe listen --forward-to localhost:3000/api/webhooks/stripe
   ```

4. Get webhook signing secret from CLI output (starts with `whsec_...`)

5. Update `.env.local`:
   ```
   STRIPE_WEBHOOK_SECRET=whsec_xxx_from_stripe_cli
   ```

6. Trigger test events:
   ```bash
   stripe trigger checkout.session.completed
   stripe trigger invoice.paid
   stripe trigger invoice.payment_failed
   stripe trigger customer.subscription.updated
   stripe trigger customer.subscription.deleted
   ```

---

## 7. Critical Constraints

**DO NOT:**
- Process webhooks without signature verification - CRITICAL SECURITY
- Trust client-sent tier changes - tier must only be updated via webhooks
- Expose `stripe_customer_id` or `stripe_subscription_id` in API responses
- Log full webhook payloads (may contain PII)
- Return 5xx status codes (Stripe will retry indefinitely)
- Hardcode price IDs in code (use environment variables)

**MUST:**
- Verify webhook signature using `stripe.webhooks.constructEvent()`
- Use service role key for webhook database operations (bypasses RLS)
- Respond within 10 seconds (Stripe timeout)
- Handle idempotency (same event may be delivered multiple times)
- Log event processing for debugging
- Update `updated_at` timestamp on profile changes

**SECURITY CRITICAL:**
- `STRIPE_WEBHOOK_SECRET` must be kept secret
- `SUPABASE_SERVICE_ROLE_KEY` must never be exposed to client
- All billing operations must use server-side code

---

## 8. Progress Log

*Updated by implementing agent during work.*

### 2026-02-17 - Initial Planning
- **Completed:** Stage architecture document created
- **Next:** Awaiting Stage 01 completion before implementation
- **Blockers:** None

---

## 9. Issues & Blockers

*Document any escalations here.*

### None - Stage is planned and ready for implementation

---

## 10. Completion Checklist

- [ ] All components built per Section 3
  - [ ] Webhook endpoint at `/api/webhooks/stripe`
  - [ ] Subscription service layer
  - [ ] Event handlers (5 handlers)
  - [ ] Feature gates utility
  - [ ] Checkout session endpoint
- [ ] All API contracts implemented per Section 4
- [ ] All database operations working per Section 5
- [ ] All tests passing per Section 6
  - [ ] Unit tests for signature verification
  - [ ] Unit tests for tier limits
  - [ ] Integration tests for webhook flows
- [ ] All constraints followed per Section 7
- [ ] Progress log updated per Section 8
- [ ] Success criteria met (Section 1)
  - [ ] Signature verification passes
  - [ ] All 5 event types handled correctly
  - [ ] Users get immediate access after checkout
  - [ ] Response time < 10 seconds

**Stage Completed:** _ | **Final Status:** Planned

---

## 11. Environment Variables Required

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_xxx                    # Stripe secret key
STRIPE_WEBHOOK_SECRET=whsec_xxx                  # From Stripe CLI or Dashboard
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxx   # For frontend
STRIPE_PRICE_SOLO=price_xxx                      # Solo tier price ID
STRIPE_PRICE_AGENCY=price_xxx                    # Agency tier price ID
STRIPE_PRICE_ENTERPRISE=price_xxx                # Enterprise tier price ID

# Supabase (already configured)
SUPABASE_SERVICE_ROLE_KEY=xxx                    # Required for webhook operations
NEXT_PUBLIC_SUPABASE_URL=xxx
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx

# App Configuration
NEXT_PUBLIC_APP_URL=http://localhost:3000        # For checkout redirect URLs
```

---

## 12. File Structure

```
frontend/
├── app/
│   └── api/
│       ├── webhooks/
│       │   └── stripe/
│       │       └── route.ts          # Webhook endpoint
│       └── checkout/
│           └── route.ts              # Checkout session creation
├── lib/
│   └── billing/
│       ├── subscription-service.ts   # Core subscription operations
│       ├── feature-gates.ts          # Tier-based feature access
│       └── handlers/
│           ├── checkout-complete.ts
│           ├── invoice-paid.ts
│           ├── invoice-failed.ts
│           ├── subscription-updated.ts
│           └── subscription-deleted.ts
```

---

*Stage Architecture Document Version: 1.0*
*Created: 2026-02-17*
*Based on: Technical PRD Section 6 - Implementation Stages (Stage 02)*
