// /frontend/lib/billing/handlers/checkout-complete.ts

import Stripe from 'stripe';
import { SubscriptionService } from '../subscription-service';

/**
 * Handle checkout.session.completed event
 * Fires when user completes Stripe Checkout
 *
 * This is the primary event for new subscriptions - it fires when:
 * - A user completes the checkout form
 * - Payment is successful
 * - A new subscription is created
 */
export async function handleCheckoutComplete(event: Stripe.Event): Promise<void> {
  const session = event.data.object as Stripe.Checkout.Session;

  const stripeCustomerId = session.customer as string;
  const stripeSubscriptionId = session.subscription as string;

  // Get price ID from session
  // Try metadata first, then line items
  let priceId = session.metadata?.priceId;

  if (!priceId && session.line_items) {
    // Fetch full session with line items if needed
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
      apiVersion: '2023-10-16',
    });
    const fullSession = await stripe.checkout.sessions.retrieve(session.id, {
      expand: ['line_items'],
    });
    priceId = fullSession.line_items?.data[0]?.price?.id;
  }

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
    tier: tier as 'free' | 'solo' | 'agency' | 'enterprise',
    status: 'active',
  });

  if (!result.success) {
    throw new Error(`Failed to update subscription: ${result.error}`);
  }

  console.log(
    `[handleCheckoutComplete] User ${result.userId} upgraded to ${tier}, subscription: ${stripeSubscriptionId}`
  );
}
