// /frontend/lib/billing/handlers/subscription-deleted.ts

import Stripe from 'stripe';
import { SubscriptionService } from '../subscription-service';

/**
 * Handle customer.subscription.deleted event
 * Fires when subscription is cancelled (end of billing period or immediately)
 *
 * This event fires for:
 * - User cancels subscription (at period end)
 * - Subscription is deleted immediately
 * - Subscription expires after grace period
 * - Admin cancels subscription
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

  console.log(
    `[handleSubscriptionDeleted] User ${result.userId} subscription cancelled, downgraded to free`
  );

  // TODO: Send cancellation confirmation email
  // This would integrate with the email service in Stage 05
}
