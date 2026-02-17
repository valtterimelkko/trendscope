// /frontend/app/api/checkout/route.ts

import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { createClient } from '@/lib/supabase/server';
import { Tier } from '@/lib/billing/feature-gates';

/**
 * Initialize Stripe client
 */
const getStripe = () => {
  return new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: '2025-02-24.acacia',
  });
};

/**
 * Map tier to Stripe price ID
 */
const PRICE_MAP: Record<Tier, string | undefined> = {
  free: undefined, // Free tier has no price
  solo: process.env.STRIPE_PRICE_SOLO,
  agency: process.env.STRIPE_PRICE_AGENCY,
  enterprise: process.env.STRIPE_PRICE_ENTERPRISE,
};

/**
 * POST /api/checkout
 *
 * Create a Stripe Checkout session for subscription upgrade
 *
 * Request body:
 * - tier: 'solo' | 'agency' | 'enterprise'
 *
 * Response:
 * - 200: { sessionId: string, url: string }
 * - 400: Invalid tier
 * - 401: Unauthorized
 * - 500: Failed to create checkout session
 */
export async function POST(request: NextRequest) {
  try {
    // Parse request body
    const body = await request.json();
    const { tier } = body as { tier: Tier };

    // Validate tier
    if (!tier || tier === 'free' || !PRICE_MAP[tier]) {
      return NextResponse.json(
        { error: 'Invalid tier. Must be solo, agency, or enterprise.' },
        { status: 400 }
      );
    }

    const priceId = PRICE_MAP[tier];
    if (!priceId) {
      return NextResponse.json(
        { error: `Price not configured for tier: ${tier}` },
        { status: 500 }
      );
    }

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

    // Get user profile
    const { data: profile, error: profileError } = await supabase
      .from('profiles')
      .select('stripe_customer_id, tier')
      .eq('id', user.id)
      .single();

    if (profileError) {
      console.error('[Checkout] Error fetching profile:', profileError);
      return NextResponse.json(
        { error: 'Failed to fetch profile' },
        { status: 500 }
      );
    }

    const stripe = getStripe();
    let customerId = profile?.stripe_customer_id;

    // Create Stripe customer if not exists
    if (!customerId) {
      const customer = await stripe.customers.create({
        email: user.email,
        metadata: {
          userId: user.id,
        },
      });
      customerId = customer.id;

      // Update profile with customer ID
      const { error: updateError } = await supabase
        .from('profiles')
        .update({ stripe_customer_id: customerId })
        .eq('id', user.id);

      if (updateError) {
        console.error('[Checkout] Error updating profile with customer ID:', updateError);
        // Continue anyway - the webhook will handle this
      }

      console.log(`[Checkout] Created Stripe customer ${customerId} for user ${user.id}`);
    }

    // Create checkout session
    const session = await stripe.checkout.sessions.create({
      customer: customerId,
      mode: 'subscription',
      payment_method_types: ['card'],
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      success_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?checkout=success&tier=${tier}`,
      cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/pricing?checkout=canceled`,
      metadata: {
        userId: user.id,
        tier,
        previousTier: profile?.tier || 'free',
      },
      subscription_data: {
        metadata: {
          userId: user.id,
          tier,
        },
      },
      allow_promotion_codes: true,
      billing_address_collection: 'required',
    });

    console.log(
      `[Checkout] Created session ${session.id} for user ${user.id}, tier: ${tier}`
    );

    return NextResponse.json({
      sessionId: session.id,
      url: session.url,
    });
  } catch (error) {
    console.error('[Checkout] Error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json(
      { error: 'Failed to create checkout session', details: errorMessage },
      { status: 500 }
    );
  }
}
