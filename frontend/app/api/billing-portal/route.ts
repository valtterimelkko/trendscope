// /frontend/app/api/billing-portal/route.ts

import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { createClient } from '@/lib/supabase/server';

/**
 * Initialize Stripe client
 */
const getStripe = () => {
  return new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: '2023-10-16',
  });
};

/**
 * POST /api/billing-portal
 *
 * Create a Stripe billing portal session for subscription management
 *
 * This allows users to:
 * - Update payment methods
 * - View invoices
 * - Cancel subscription
 * - Update billing information
 *
 * Response:
 * - 200: { url: string }
 * - 401: Unauthorized
 * - 400: No active subscription
 * - 500: Failed to create portal session
 */
export async function POST(request: NextRequest) {
  try {
    // Get authenticated user
    const supabase = await createClient();
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Get user profile with Stripe customer ID
    const { data: profile, error: profileError } = await supabase
      .from('profiles')
      .select('stripe_customer_id, stripe_subscription_id, tier')
      .eq('id', user.id)
      .single();

    if (profileError || !profile) {
      console.error('[Billing Portal] Error fetching profile:', profileError);
      return NextResponse.json(
        { error: 'Failed to fetch profile' },
        { status: 500 }
      );
    }

    // Check if user has a Stripe customer ID
    if (!profile.stripe_customer_id) {
      return NextResponse.json(
        { error: 'No billing account found' },
        { status: 400 }
      );
    }

    const stripe = getStripe();

    // Create billing portal session
    const portalSession = await stripe.billingPortal.sessions.create({
      customer: profile.stripe_customer_id,
      return_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?portal=return`,
    });

    console.log(
      `[Billing Portal] Created portal session for user ${user.id}, customer: ${profile.stripe_customer_id}`
    );

    return NextResponse.json({
      url: portalSession.url,
    });
  } catch (error) {
    console.error('[Billing Portal] Error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json(
      { error: 'Failed to create billing portal session', details: errorMessage },
      { status: 500 }
    );
  }
}
