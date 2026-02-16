import { headers } from 'next/headers'
import { NextResponse } from 'next/server'
import Stripe from 'stripe'
import { createClient } from '@supabase/supabase-js'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-06-20',
})

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

// Feature limits and flags by plan tier
const PLAN_CONFIG: Record<string, {
  limits: { posts: number; storage_mb: number; scheduled: number; members: number; monthly_credits: number };
  featureFlags: Record<string, boolean>;
}> = {
  starter: {
    limits: { posts: 10, storage_mb: 500, scheduled: 5, members: 1, monthly_credits: 1000 },
    featureFlags: {
      seo_tools: false,
      custom_categories: false,
      api_access: false,
      analytics_dashboard: false,
      custom_domain: false,
      white_label: false,
    },
  },
  creator: {
    limits: { posts: 100, storage_mb: 10240, scheduled: 50, members: 3, monthly_credits: 10000 },
    featureFlags: {
      seo_tools: true,
      custom_categories: true,
      api_access: false,
      analytics_dashboard: false,
      custom_domain: false,
      white_label: false,
    },
  },
  studio: {
    limits: { posts: -1, storage_mb: 102400, scheduled: -1, members: 10, monthly_credits: -1 },
    featureFlags: {
      seo_tools: true,
      custom_categories: true,
      api_access: true,
      analytics_dashboard: true,
      custom_domain: true,
      white_label: true,
    },
  },
}

// Credit pack configuration
const CREDIT_PACKS: Record<string, number> = {
  price_credits_5k: 5000,
  price_credits_10k: 10000,
  price_credits_25k: 25000,
}

// Determine tier from price ID
function getTierFromPriceId(priceId: string): string {
  if (priceId.includes('studio')) return 'studio'
  if (priceId.includes('creator')) return 'creator'
  return 'starter'
}

export async function POST(request: Request) {
  const body = await request.text()
  const headersList = await headers()
  const signature = headersList.get('stripe-signature')!

  let event: Stripe.Event

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    )
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown error'
    console.error('Webhook signature verification failed:', message)
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
  }

  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session

        // Handle credit pack purchase (one-time payment)
        if (session.mode === 'payment') {
          const workspaceId = session.metadata?.workspace_id
          const priceId = session.metadata?.price_id
          const creditAmount = priceId ? CREDIT_PACKS[priceId] : 0

          if (workspaceId && creditAmount > 0) {
            // Add credits to ledger
            await supabase.rpc('add_credits_from_purchase', {
              p_workspace_id: workspaceId,
              p_amount: creditAmount,
              p_stripe_payment_intent_id: session.payment_intent as string,
              p_description: `Credit pack purchase: ${creditAmount.toLocaleString()} credits`,
            })
          }
          break
        }

        // Handle subscription checkout
        const subscription = await stripe.subscriptions.retrieve(
          session.subscription as string
        )

        const workspaceId = session.metadata?.workspace_id
        const tier = session.metadata?.tier || 'creator'
        const config = PLAN_CONFIG[tier] || PLAN_CONFIG.creator

        if (workspaceId) {
          // Create or update customer record
          await supabase.from('customers').upsert({
            workspace_id: workspaceId,
            stripe_customer_id: session.customer as string,
          })

          // Create subscription record with feature limits
          await supabase.from('subscriptions').upsert({
            workspace_id: workspaceId,
            stripe_subscription_id: subscription.id,
            stripe_customer_id: session.customer as string,
            status: subscription.status,
            price_id: subscription.items.data[0].price.id,
            post_limit: config.limits.posts,
            storage_limit_mb: config.limits.storage_mb,
            scheduled_limit: config.limits.scheduled,
            member_limit: config.limits.members,
            current_period_start: new Date(subscription.current_period_start * 1000).toISOString(),
            current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
            // Trial support
            trial_start: subscription.trial_start
              ? new Date(subscription.trial_start * 1000).toISOString()
              : null,
            trial_end: subscription.trial_end
              ? new Date(subscription.trial_end * 1000).toISOString()
              : null,
            // Feature flags and tier
            plan_tier: tier,
            feature_flags: config.featureFlags,
          })

          // Add monthly subscription credits
          if (config.limits.monthly_credits > 0) {
            await supabase.rpc('add_subscription_credits', {
              p_workspace_id: workspaceId,
              p_amount: config.limits.monthly_credits,
              p_description: `Monthly ${tier} subscription credits`,
            })
          }
        }
        break
      }

      case 'customer.created': {
        const customer = event.data.object as Stripe.Customer
        if (customer.metadata?.workspace_id) {
          await supabase.from('customers').upsert({
            workspace_id: customer.metadata.workspace_id,
            stripe_customer_id: customer.id,
          })
        }
        break
      }

      case 'customer.subscription.created':
      case 'customer.subscription.updated': {
        const subscription = event.data.object as Stripe.Subscription

        // Get tier from price metadata or product
        const priceId = subscription.items.data[0].price.id
        const tier = getTierFromPriceId(priceId)
        const config = PLAN_CONFIG[tier] || PLAN_CONFIG.creator

        await supabase
          .from('subscriptions')
          .update({
            status: subscription.status,
            price_id: priceId,
            post_limit: config.limits.posts,
            storage_limit_mb: config.limits.storage_mb,
            scheduled_limit: config.limits.scheduled,
            member_limit: config.limits.members,
            current_period_start: new Date(subscription.current_period_start * 1000).toISOString(),
            current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
            cancel_at_period_end: subscription.cancel_at_period_end,
            // Trial support
            trial_start: subscription.trial_start
              ? new Date(subscription.trial_start * 1000).toISOString()
              : null,
            trial_end: subscription.trial_end
              ? new Date(subscription.trial_end * 1000).toISOString()
              : null,
            // Feature flags and tier
            plan_tier: tier,
            feature_flags: config.featureFlags,
          })
          .eq('stripe_subscription_id', subscription.id)
        break
      }

      case 'customer.subscription.deleted': {
        const subscription = event.data.object as Stripe.Subscription

        // Reset to starter limits
        const starterConfig = PLAN_CONFIG.starter

        await supabase
          .from('subscriptions')
          .update({
            status: 'canceled',
            canceled_at: new Date().toISOString(),
            post_limit: starterConfig.limits.posts,
            storage_limit_mb: starterConfig.limits.storage_mb,
            scheduled_limit: starterConfig.limits.scheduled,
            member_limit: starterConfig.limits.members,
            plan_tier: 'starter',
            feature_flags: starterConfig.featureFlags,
          })
          .eq('stripe_subscription_id', subscription.id)
        break
      }

      case 'customer.subscription.trial_will_end': {
        const subscription = event.data.object as Stripe.Subscription
        // Update trial_end in database (3 days before expiry)
        await supabase
          .from('subscriptions')
          .update({
            trial_end: subscription.trial_end
              ? new Date(subscription.trial_end * 1000).toISOString()
              : null,
          })
          .eq('stripe_subscription_id', subscription.id)
        // TODO: Trigger email notification via your email service
        console.log(`Trial ending soon for subscription ${subscription.id}`)
        break
      }

      case 'invoice.payment_succeeded': {
        const invoice = event.data.object as Stripe.Invoice

        if (invoice.subscription) {
          // Clear dunning fields
          await supabase
            .from('subscriptions')
            .update({
              status: 'active',
              dunning_started_at: null,
              dunning_emails_sent: 0,
              grace_period_until: null,
            })
            .eq('stripe_subscription_id', invoice.subscription as string)

          // Add monthly credits if this is a renewal (not first payment)
          if (invoice.billing_reason === 'subscription_cycle') {
            const { data: sub } = await supabase
              .from('subscriptions')
              .select('workspace_id, plan_tier')
              .eq('stripe_subscription_id', invoice.subscription as string)
              .single()

            if (sub?.workspace_id && sub.plan_tier) {
              const config = PLAN_CONFIG[sub.plan_tier]
              if (config && config.limits.monthly_credits > 0) {
                await supabase.rpc('add_subscription_credits', {
                  p_workspace_id: sub.workspace_id,
                  p_amount: config.limits.monthly_credits,
                  p_description: `Monthly ${sub.plan_tier} subscription credits renewal`,
                })
              }
            }
          }
        }
        break
      }

      case 'invoice.payment_failed': {
        const invoice = event.data.object as Stripe.Invoice

        if (invoice.subscription) {
          const gracePeriodEnd = new Date()
          gracePeriodEnd.setDate(gracePeriodEnd.getDate() + 7) // 7 day grace period

          await supabase
            .from('subscriptions')
            .update({
              status: 'past_due',
              dunning_started_at: new Date().toISOString(),
              grace_period_until: gracePeriodEnd.toISOString(),
            })
            .eq('stripe_subscription_id', invoice.subscription as string)
        }
        break
      }

      case 'invoice.payment_action_required': {
        const invoice = event.data.object as Stripe.Invoice
        // Customer needs to take action (e.g., 3D Secure)
        if (invoice.subscription) {
          const gracePeriodEnd = new Date()
          gracePeriodEnd.setDate(gracePeriodEnd.getDate() + 7)

          await supabase
            .from('subscriptions')
            .update({
              dunning_started_at: new Date().toISOString(),
              grace_period_until: gracePeriodEnd.toISOString(),
            })
            .eq('stripe_subscription_id', invoice.subscription as string)
        }
        break
      }

      case 'invoice.upcoming': {
        const invoice = event.data.object as Stripe.Invoice
        console.log(`Upcoming invoice for subscription ${invoice.subscription}`)
        break
      }

      default:
        console.log(`Unhandled event type: ${event.type}`)
    }

    return NextResponse.json({ received: true })
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown error'
    console.error('Webhook handler error:', message)
    return NextResponse.json({ error: 'Webhook handler failed' }, { status: 500 })
  }
}
