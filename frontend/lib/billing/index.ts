// /frontend/lib/billing/index.ts

/**
 * Billing module exports
 *
 * This module handles all Stripe-related functionality:
 * - Subscription management via webhooks
 * - Feature gates based on tier
 * - Checkout session creation
 */

// Core services
export { SubscriptionService } from './subscription-service';
export type { SubscriptionUpdate, SubscriptionResult } from './subscription-service';

// Feature gates
export {
  TIER_LIMITS,
  TIER_DISPLAY_NAMES,
  TIER_DESCRIPTIONS,
  canAddNiche,
  canUseSlackIntegration,
  canUseAgencyFeatures,
  canAddClient,
  getAlertLatency,
  getAlertLatencyHours,
  shouldSendAlert,
  getMaxNiches,
  getMaxAlerts,
  getVelocityThreshold,
  getTierPrice,
  isPaidTier,
  compareTiers,
  useFeatureGates,
  getFeatureGates,
} from './feature-gates';
export type { Tier, TierLimits } from './feature-gates';

// Webhook handlers (for internal use)
export { handleCheckoutComplete } from './handlers/checkout-complete';
export { handleInvoicePaid } from './handlers/invoice-paid';
export { handleInvoiceFailed } from './handlers/invoice-failed';
export { handleSubscriptionUpdated } from './handlers/subscription-updated';
export { handleSubscriptionDeleted } from './handlers/subscription-deleted';
