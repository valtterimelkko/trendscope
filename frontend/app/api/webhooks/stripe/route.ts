// /frontend/app/api/webhooks/stripe/route.ts

import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { handleCheckoutComplete } from '@/lib/billing/handlers/checkout-complete';
import { handleInvoicePaid } from '@/lib/billing/handlers/invoice-paid';
import { handleInvoiceFailed } from '@/lib/billing/handlers/invoice-failed';
import { handleSubscriptionUpdated } from '@/lib/billing/handlers/subscription-updated';
import { handleSubscriptionDeleted } from '@/lib/billing/handlers/subscription-deleted';

/**
 * Initialize Stripe client
 */
const getStripe = () => {
  return new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: '2025-02-24.acacia',
  });
};

/**
 * Event type to handler mapping
 */
const eventHandlers: Record<string, (event: Stripe.Event) => Promise<void>> = {
  'checkout.session.completed': handleCheckoutComplete,
  'invoice.paid': handleInvoicePaid,
  'invoice.payment_failed': handleInvoiceFailed,
  'customer.subscription.updated': handleSubscriptionUpdated,
  'customer.subscription.deleted': handleSubscriptionDeleted,
};

/**
 * POST /api/webhooks/stripe
 *
 * Stripe webhook endpoint for subscription events
 *
 * Security: ALWAYS verifies webhook signature using stripe.webhooks.constructEvent()
 *
 * Events Handled:
 * - checkout.session.completed: Activate subscription
 * - invoice.paid: Confirm payment, update tier
 * - invoice.payment_failed: Grace period handling
 * - customer.subscription.updated: Tier changes
 * - customer.subscription.deleted: Cancellation
 *
 * Response:
 * - 200: Event received (handled or unhandled)
 * - 400: Invalid signature or missing signature header
 */
export async function POST(request: NextRequest) {
  const stripe = getStripe();
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  // Get raw body as text (required for signature verification)
  const body = await request.text();
  const signature = request.headers.get('stripe-signature');

  // Validate signature header exists
  if (!signature) {
    console.error('[Stripe Webhook] Missing stripe-signature header');
    return NextResponse.json(
      { error: 'Missing signature' },
      { status: 400 }
    );
  }

  // Validate webhook secret is configured
  if (!webhookSecret) {
    console.error('[Stripe Webhook] STRIPE_WEBHOOK_SECRET not configured');
    return NextResponse.json(
      { error: 'Webhook secret not configured' },
      { status: 500 }
    );
  }

  let event: Stripe.Event;

  try {
    // CRITICAL SECURITY: Verify webhook signature
    // This ensures the request genuinely came from Stripe
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    console.error('[Stripe Webhook] Signature verification failed:', errorMessage);
    return NextResponse.json(
      { error: 'Invalid signature' },
      { status: 400 }
    );
  }

  // Log event receipt
  console.log(`[Stripe Webhook] Received event: ${event.type} (${event.id})`);

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
    console.log(`[Stripe Webhook] Successfully processed: ${event.type} (${event.id})`);
    return NextResponse.json({ received: true, handled: true });
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    console.error(
      `[Stripe Webhook] Error processing ${event.type} (${event.id}):`,
      errorMessage
    );

    // Return 200 to acknowledge receipt but indicate error
    // We don't return 5xx because Stripe will retry indefinitely
    // For business logic errors, we should handle them and not retry
    return NextResponse.json({
      received: true,
      handled: false,
      error: errorMessage,
    });
  }
}
