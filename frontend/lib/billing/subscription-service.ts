// /frontend/lib/billing/subscription-service.ts

import { createClient } from '@supabase/supabase-js';
import Stripe from 'stripe';

/**
 * Create Supabase admin client for webhook operations
 * Uses service role key to bypass RLS for subscription updates
 */
function getSupabaseAdmin() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
}

/**
 * Get tier from Stripe price ID
 */
function getPriceToTierMap(): Record<string, string> {
  return {
    [process.env.STRIPE_PRICE_SOLO || '']: 'solo',
    [process.env.STRIPE_PRICE_AGENCY || '']: 'agency',
    [process.env.STRIPE_PRICE_ENTERPRISE || '']: 'enterprise',
  };
}

export interface SubscriptionUpdate {
  stripeCustomerId: string;
  stripeSubscriptionId: string | null;
  tier: 'free' | 'solo' | 'agency' | 'enterprise';
  status: 'active' | 'paused' | 'cancelled';
}

export interface SubscriptionResult {
  success: boolean;
  userId?: string;
  error?: string;
}

export class SubscriptionService {
  /**
   * Update user subscription based on Stripe data
   * Uses service role key to bypass RLS policies
   */
  static async updateSubscription(
    stripeCustomerId: string,
    data: Partial<SubscriptionUpdate>
  ): Promise<SubscriptionResult> {
    const supabase = getSupabaseAdmin();

    // Find user by stripe_customer_id
    const { data: profile, error: findError } = await supabase
      .from('profiles')
      .select('id, tier, status')
      .eq('stripe_customer_id', stripeCustomerId)
      .single();

    if (findError || !profile) {
      console.error('[SubscriptionService] User not found for customer:', stripeCustomerId, findError);
      return { success: false, error: 'User not found' };
    }

    // Update profile with new subscription data
    const updateData: Record<string, unknown> = {
      updated_at: new Date().toISOString(),
    };

    if (data.tier !== undefined) {
      updateData.tier = data.tier;
    }
    if (data.status !== undefined) {
      updateData.status = data.status;
    }
    if (data.stripeSubscriptionId !== undefined) {
      updateData.stripe_subscription_id = data.stripeSubscriptionId;
    }

    const { error: updateError } = await supabase
      .from('profiles')
      .update(updateData)
      .eq('id', profile.id);

    if (updateError) {
      console.error('[SubscriptionService] Failed to update profile:', updateError);
      return { success: false, error: updateError.message };
    }

    console.log(
      `[SubscriptionService] Updated user ${profile.id}: tier=${data.tier || profile.tier}, status=${data.status || profile.status}`
    );
    return { success: true, userId: profile.id };
  }

  /**
   * Get tier from Stripe price ID
   */
  static getTierFromPrice(priceId: string): string {
    const priceMap = getPriceToTierMap();
    return priceMap[priceId] || 'free';
  }

  /**
   * Create Stripe customer for user if not exists
   * Used when initiating a checkout session
   */
  static async ensureStripeCustomer(
    userId: string,
    email: string
  ): Promise<{ stripeCustomerId: string } | { error: string }> {
    const supabase = getSupabaseAdmin();

    const { data: profile } = await supabase
      .from('profiles')
      .select('stripe_customer_id')
      .eq('id', userId)
      .single();

    if (profile?.stripe_customer_id) {
      return { stripeCustomerId: profile.stripe_customer_id };
    }

    // Create new Stripe customer
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
      apiVersion: '2023-10-16',
    });
    const customer = await stripe.customers.create({
      email,
      metadata: { userId },
    });

    // Update profile with customer ID
    await supabase
      .from('profiles')
      .update({ stripe_customer_id: customer.id })
      .eq('id', userId);

    console.log(`[SubscriptionService] Created Stripe customer ${customer.id} for user ${userId}`);
    return { stripeCustomerId: customer.id };
  }

  /**
   * Get user profile by Stripe customer ID
   */
  static async getProfileByCustomerId(stripeCustomerId: string): Promise<{
    id: string;
    tier: string;
    status: string;
    email: string;
  } | null> {
    const supabase = getSupabaseAdmin();

    const { data: profile, error } = await supabase
      .from('profiles')
      .select('id, tier, status, email')
      .eq('stripe_customer_id', stripeCustomerId)
      .single();

    if (error || !profile) {
      return null;
    }

    return profile;
  }

  /**
   * Check if a subscription event has already been processed (idempotency)
   * Stripe may send the same event multiple times
   */
  static async isEventProcessed(eventId: string): Promise<boolean> {
    const supabase = getSupabaseAdmin();

    // Check if we have a record of this event
    const { data } = await supabase
      .from('stripe_events')
      .select('id')
      .eq('id', eventId)
      .single();

    return !!data;
  }

  /**
   * Mark an event as processed
   */
  static async markEventProcessed(eventId: string, eventType: string): Promise<void> {
    const supabase = getSupabaseAdmin();

    await supabase.from('stripe_events').insert({
      id: eventId,
      type: eventType,
      processed_at: new Date().toISOString(),
    });
  }
}
