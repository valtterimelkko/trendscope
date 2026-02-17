// /frontend/lib/billing/handlers/subscription-updated.ts

import Stripe from 'stripe';
import { SubscriptionService } from '../subscription-service';

/**
 * Handle customer.subscription.updated event
 * Fires when subscription is upgraded/downgraded or status changes
 *
 * This event fires for:
 * - Plan changes (tier upgrades/downgrades)
 * - Status changes (active -> past_due, etc.)
 * - Billing cycle changes
 * - Trial conversions
 */
export async function handleSubscriptionUpdated(event: Stripe.Event): Promise<void> {
  const subscription = event.data.object as Stripe.Subscription;

  const stripeCustomerId = subscription.customer as string;
  const priceId = subscription.items.data[0]?.price?.id;

  // Map Stripe subscription status to our status
  const statusMap: Record<string, 'active' | 'paused' | 'cancelled'> = {
    active: 'active',
    trialing: 'active',
    past_due: 'paused',
    unpaid: 'paused',
    canceled: 'cancelled',
    incomplete: 'paused',
    incomplete_expired: 'cancelled',
  };

  const status = statusMap[subscription.status] || 'paused';
  const tier = priceId
    ? SubscriptionService.getTierFromPrice(priceId)
    : 'free';

  const result = await SubscriptionService.updateSubscription(stripeCustomerId, {
    stripeCustomerId,
    stripeSubscriptionId: subscription.id,
    tier: tier as 'free' | 'solo' | 'agency' | 'enterprise',
    status,
  });

  if (!result.success) {
    throw new Error(`Failed to update subscription: ${result.error}`);
  }

  console.log(
    `[handleSubscriptionUpdated] User ${result.userId} subscription updated: tier=${tier}, status=${status}`
  );
}
