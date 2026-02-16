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

// Feature flags by plan tier
const FEATURE_FLAGS: Record<string, Record<string, boolean>> = {
  starter: {
    api_access: false,
    custom_fields: false,
    priority_support: false,
    advanced_integrations: false,
  },
  pro: {
    api_access: true,
    custom_fields: true,
    priority_support: true,
    advanced_integrations: true,
  },
  enterprise: {
    api_access: true,
    custom_fields: true,
    priority_support: true,
    advanced_integrations: true,
    sso_saml: true,
    audit_logs: true,
    sla_guarantee: true,
  },
}

// Determine tier from price ID
function getTierFromPriceId(priceId: string): string {
  if (priceId.includes('enterprise')) return 'enterprise'
  if (priceId.includes('pro')) return 'pro'
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

        // Get subscription details
        const subscription = await stripe.subscriptions.retrieve(
          session.subscription as string
        )

        const workspaceId = session.metadata?.workspace_id
        const seatCount = parseInt(session.metadata?.seat_count || '5')
        const priceId = subscription.items.data[0].price.id
        const tier = getTierFromPriceId(priceId)
        const featureFlags = FEATURE_FLAGS[tier] || FEATURE_FLAGS.starter

        if (workspaceId) {
          // Create or update customer record
          await supabase.from('customers').upsert({
            workspace_id: workspaceId,
            stripe_customer_id: session.customer as string,
          })

          // Create subscription record
          await supabase.from('subscriptions').upsert({
            id: subscription.id,
            workspace_id: workspaceId,
            stripe_subscription_id: subscription.id,
            stripe_customer_id: session.customer as string,
            status: subscription.status,
            price_id: priceId,
            quantity: seatCount,
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
            feature_flags: featureFlags,
          })
        }
        break
      }

      case 'customer.subscription.created':
      case 'customer.subscription.updated': {
        const subscription = event.data.object as Stripe.Subscription

        // Update subscription in database
        const { data: existingSub } = await supabase
          .from('subscriptions')
          .select('workspace_id')
          .eq('stripe_subscription_id', subscription.id)
          .single()

        if (existingSub) {
          // Calculate seat count from quantity
          const seatCount = subscription.items.data[0].quantity || 1
          const priceId = subscription.items.data[0].price.id
          const tier = getTierFromPriceId(priceId)
          const featureFlags = FEATURE_FLAGS[tier] || FEATURE_FLAGS.starter

          await supabase
            .from('subscriptions')
            .update({
              status: subscription.status,
              price_id: priceId,
              quantity: seatCount,
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
              feature_flags: featureFlags,
            })
            .eq('stripe_subscription_id', subscription.id)

          // Record seat usage
          await supabase.from('seat_usage').insert({
            workspace_id: existingSub.workspace_id,
            seat_count: seatCount,
            billable_seats: seatCount,
            recorded_at: new Date().toISOString(),
          })
        }
        break
      }

      case 'customer.subscription.deleted': {
        const subscription = event.data.object as Stripe.Subscription

        await supabase
          .from('subscriptions')
          .update({
            status: 'canceled',
            canceled_at: new Date().toISOString(),
            feature_flags: FEATURE_FLAGS.starter,
            plan_tier: 'starter',
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
          await supabase
            .from('subscriptions')
            .update({
              status: 'active',
              // Clear dunning fields on successful payment
              dunning_started_at: null,
              dunning_emails_sent: 0,
              grace_period_until: null,
            })
            .eq('stripe_subscription_id', invoice.subscription as string)
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
        // Log for seat reconciliation opportunity
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
