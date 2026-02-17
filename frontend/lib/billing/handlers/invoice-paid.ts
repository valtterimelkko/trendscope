// /frontend/lib/billing/handlers/invoice-paid.ts

import Stripe from 'stripe';
import { SubscriptionService } from '../subscription-service';

/**
 * Handle invoice.paid event
 * Fires when a subscription payment succeeds
 *
 * This event fires for:
 * - Initial subscription payment
 * - Recurring subscription renewals
 * - One-time invoice payments
 *
 * We use this to ensure the subscription is active and tier is correct
 */
export async function handleInvoicePaid(event: Stripe.Event): Promise<void> {
  const invoice = event.data.object as Stripe.Invoice;

  const stripeCustomerId = invoice.customer as string;
  const stripeSubscriptionId = invoice.subscription as string;

  // Only process subscription invoices (not one-time payments)
  if (!stripeSubscriptionId) {
    console.log('[handleInvoicePaid] Skipping non-subscription invoice');
    return;
  }

  // Get subscription details to determine current tier
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: '2023-10-16',
  });
  const subscription = await stripe.subscriptions.retrieve(stripeSubscriptionId);
  const priceId = subscription.items.data[0]?.price?.id;

  const tier = priceId
    ? SubscriptionService.getTierFromPrice(priceId)
    : 'solo';

  // Ensure subscription is active
  const result = await SubscriptionService.updateSubscription(stripeCustomerId, {
    stripeCustomerId,
    stripeSubscriptionId,
    tier: tier as 'free' | 'solo' | 'agency' | 'enterprise',
    status: 'active',
  });

  if (!result.success) {
    throw new Error(`Failed to confirm subscription: ${result.error}`);
  }

  console.log(
    `[handleInvoicePaid] Subscription confirmed for user ${result.userId}, tier=${tier}`
  );
}
