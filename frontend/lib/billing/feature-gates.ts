// /frontend/lib/billing/feature-gates.ts

/**
 * Tier limits and feature access configuration
 *
 * These limits define what each subscription tier can access.
 * Used for both frontend UI gating and backend validation.
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
    price: 0,
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
    price: 29,
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
    price: 99,
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
    price: 299,
  },
} as const;

export type Tier = keyof typeof TIER_LIMITS;

export type TierLimits = (typeof TIER_LIMITS)[Tier];

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
 * Check if user can add more clients (agency feature)
 */
export function canAddClient(currentTier: Tier, currentCount: number): boolean {
  return currentCount < TIER_LIMITS[currentTier].maxClients;
}

/**
 * Get alert latency for tier (in milliseconds)
 */
export function getAlertLatency(tier: Tier): number {
  return TIER_LIMITS[tier].alertLatency;
}

/**
 * Get alert latency for tier (in hours, for display)
 */
export function getAlertLatencyHours(tier: Tier): number {
  const latency = TIER_LIMITS[tier].alertLatency;
  return latency === 0 ? 0 : latency / (60 * 60 * 1000);
}

/**
 * Check if alert should be sent based on velocity threshold
 * Higher velocity = more confident trend detection
 */
export function shouldSendAlert(tier: Tier, velocityScore: number): boolean {
  return velocityScore >= TIER_LIMITS[tier].velocityThreshold;
}

/**
 * Get maximum niches for tier
 */
export function getMaxNiches(tier: Tier): number {
  return TIER_LIMITS[tier].niches;
}

/**
 * Get maximum alerts for tier
 */
export function getMaxAlerts(tier: Tier): number {
  return TIER_LIMITS[tier].maxAlerts;
}

/**
 * Get velocity threshold for tier
 */
export function getVelocityThreshold(tier: Tier): number {
  return TIER_LIMITS[tier].velocityThreshold;
}

/**
 * Get tier price (for display)
 */
export function getTierPrice(tier: Tier): number {
  return TIER_LIMITS[tier].price;
}

/**
 * Check if tier is paid (not free)
 */
export function isPaidTier(tier: Tier): boolean {
  return tier !== 'free';
}

/**
 * Compare tiers for upgrade/downgrade detection
 * Returns: 1 if tier1 > tier2, -1 if tier1 < tier2, 0 if equal
 */
export function compareTiers(tier1: Tier, tier2: Tier): number {
  const tierOrder: Tier[] = ['free', 'solo', 'agency', 'enterprise'];
  const index1 = tierOrder.indexOf(tier1);
  const index2 = tierOrder.indexOf(tier2);
  return Math.sign(index1 - index2);
}

/**
 * Feature gate object for use in React components
 * Call this from a component that has access to the user's tier
 */
export function useFeatureGates(tier: Tier) {
  return {
    limits: TIER_LIMITS[tier],
    canAddNiche: (count: number) => canAddNiche(tier, count),
    canUseSlack: () => canUseSlackIntegration(tier),
    canUseAgency: () => canUseAgencyFeatures(tier),
    canAddClient: (count: number) => canAddClient(tier, count),
    alertLatency: getAlertLatency(tier),
    alertLatencyHours: getAlertLatencyHours(tier),
    maxNiches: getMaxNiches(tier),
    maxAlerts: getMaxAlerts(tier),
    velocityThreshold: getVelocityThreshold(tier),
    isPaid: isPaidTier(tier),
  };
}

/**
 * Server-side feature gate check
 * Use this in API routes and server components
 */
export function getFeatureGates(tier: Tier) {
  return {
    tier,
    limits: TIER_LIMITS[tier],
    canAddNiche: (count: number) => canAddNiche(tier, count),
    canUseSlack: () => canUseSlackIntegration(tier),
    canUseAgency: () => canUseAgencyFeatures(tier),
    canAddClient: (count: number) => canAddClient(tier, count),
    shouldSendAlert: (velocityScore: number) => shouldSendAlert(tier, velocityScore),
  };
}

/**
 * Tier display names for UI
 */
export const TIER_DISPLAY_NAMES: Record<Tier, string> = {
  free: 'Free',
  solo: 'Solo',
  agency: 'Agency',
  enterprise: 'Enterprise',
};

/**
 * Tier descriptions for UI
 */
export const TIER_DESCRIPTIONS: Record<Tier, string> = {
  free: 'Perfect for getting started with trend detection',
  solo: 'For individual creators who need faster alerts',
  agency: 'Manage multiple clients with dedicated workspaces',
  enterprise: 'Real-time alerts for high-volume operations',
};
