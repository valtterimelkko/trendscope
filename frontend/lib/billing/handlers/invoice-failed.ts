// /frontend/lib/billing/handlers/invoice-failed.ts

import Stripe from 'stripe';
import { SubscriptionService } from '../subscription-service';

/**
 * Handle invoice.payment_failed event
 * Fires when a subscription payment fails
 *
 * Grace Period Logic:
 * - First failure: Log warning, keep access (Stripe will retry)
 * - After final attempt: Downgrade to free tier, set status to paused
 *
 * Stripe typically retries payments:
 * - Up to 4 attempts over ~2 weeks
 * - Configurable in Stripe Dashboard
 */
export async function handleInvoiceFailed(event: Stripe.Event): Promise<void> {
  const invoice = event.data.object as Stripe.Invoice;

  const stripeCustomerId = invoice.customer as string;
  const stripeSubscriptionId = invoice.subscription as string;
  const attemptCount = invoice.attempt_count || 1;

  console.warn(
    `[handleInvoiceFailed] Payment failed for customer ${stripeCustomerId}, attempt ${attemptCount}`
  );

  // Only process subscription invoices (not one-time payments)
  if (!stripeSubscriptionId) {
    console.log('[handleInvoiceFailed] Skipping non-subscription invoice failure');
    return;
  }

  // Check if this is the final attempt (Stripe typically retries 3-4 times)
  // We consider attempt 4+ as final to give maximum grace period
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

    console.log(
      `[handleInvoiceFailed] User ${result.userId} downgraded to free after final payment failure`
    );

    // TODO: Send email notification about payment failure and account downgrade
    // This would integrate with the email service in Stage 05
  } else {
    // Not final attempt - just log, Stripe will retry
    console.log(
      `[handleInvoiceFailed] Payment will be retried by Stripe (attempt ${attemptCount}/4)`
    );

    // Update status to indicate payment issue (but don't change tier yet)
    await SubscriptionService.updateSubscription(stripeCustomerId, {
      stripeCustomerId,
      status: 'paused', // Temporarily pause until payment succeeds
    });
  }
}
