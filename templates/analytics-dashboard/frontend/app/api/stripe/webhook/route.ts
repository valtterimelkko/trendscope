import { headers } from 'next/headers'
import { NextResponse } from 'next/server'
import Stripe from 'stripe'
import { createServiceClient } from '@/lib/supabase/server'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-06-20',
})

const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!

// Feature flags by plan tier
const FEATURE_FLAGS: Record<string, Record<string, boolean>> = {
  starter: {
    exports: false,
    api_access: false,
    custom_events: false,
    team_collaboration: false,
    priority_support: false,
  },
  pro: {
    exports: true,
    api_access: true,
    custom_events: true,
    team_collaboration: true,
    priority_support: true,
  },
  enterprise: {
    exports: true,
    api_access: true,
    custom_events: true,
    team_collaboration: true,
    priority_support: true,
    custom_integrations: true,
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
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret)
  } catch (err) {
    console.error('Webhook signature verification failed:', err)
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
  }

  const supabase = createServiceClient()

  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session
        // Link customer to user if needed
        if (session.customer && session.metadata?.user_id) {
          await supabase.from('customers').upsert({
            id: session.metadata.user_id,
            stripe_customer_id: session.customer as string,
          })
        }
        break
      }

      case 'customer.created': {
        const customer = event.data.object as Stripe.Customer
        if (customer.metadata?.supabase_user_id) {
          await supabase.from('customers').upsert({
            id: customer.metadata.supabase_user_id,
            stripe_customer_id: customer.id,
          })
        }
        break
      }

      case 'customer.subscription.created':
      case 'customer.subscription.updated': {
        const subscription = event.data.object as Stripe.Subscription
        const priceId = subscription.items.data[0]?.price.id || ''
        const tier = getTierFromPriceId(priceId)
        const featureFlags = FEATURE_FLAGS[tier] || FEATURE_FLAGS.starter

        await supabase.from('subscriptions').upsert({
          id: subscription.id,
          user_id: subscription.metadata.user_id,
          status: subscription.status,
          price_id: priceId,
          quantity: subscription.items.data[0]?.quantity || 1,
          cancel_at_period_end: subscription.cancel_at_period_end,
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
        break
      }

      case 'customer.subscription.deleted': {
        const subscription = event.data.object as Stripe.Subscription
        await supabase
          .from('subscriptions')
          .update({
            status: 'canceled',
            feature_flags: FEATURE_FLAGS.starter,
            plan_tier: 'starter',
          })
          .eq('id', subscription.id)
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
          .eq('id', subscription.id)
        // TODO: Trigger email notification via your email service
        console.log(`Trial ending soon for subscription ${subscription.id}`)
        break
      }

      case 'invoice.payment_succeeded': {
        const invoice = event.data.object as Stripe.Invoice
        // Update subscription status to active if it was past_due
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
            .eq('id', invoice.subscription as string)
        }
        break
      }

      case 'invoice.payment_failed': {
        const invoice = event.data.object as Stripe.Invoice
        // Mark subscription as past_due and start grace period
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
            .eq('id', invoice.subscription as string)
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
            .eq('id', invoice.subscription as string)
        }
        break
      }

      case 'invoice.upcoming': {
        const invoice = event.data.object as Stripe.Invoice
        // Cache upcoming invoice for UI display (usage-based billing preview)
        if (invoice.customer && invoice.subscription) {
          // Get user_id from subscription
          const { data: sub } = await supabase
            .from('subscriptions')
            .select('user_id')
            .eq('id', invoice.subscription as string)
            .single()

          if (sub?.user_id) {
            await supabase.from('upcoming_invoices').upsert({
              user_id: sub.user_id,
              stripe_customer_id: invoice.customer as string,
              amount_due: invoice.amount_due,
              currency: invoice.currency,
              period_start: invoice.period_start
                ? new Date(invoice.period_start * 1000).toISOString()
                : null,
              period_end: invoice.period_end
                ? new Date(invoice.period_end * 1000).toISOString()
                : null,
              cached_at: new Date().toISOString(),
            })
          }
        }
        break
      }

      case 'billing.meter.error_report_triggered': {
        // Log meter errors for debugging
        console.error('Stripe Meter error report:', JSON.stringify(event.data.object, null, 2))
        break
      }

      default:
        console.log(`Unhandled event type: ${event.type}`)
    }

    return NextResponse.json({ received: true })
  } catch (error) {
    console.error('Webhook handler error:', error)
    return NextResponse.json(
      { error: 'Webhook handler failed' },
      { status: 500 }
    )
  }
}
