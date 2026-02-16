/**
 * Stripe Mock Utilities
 *
 * Provides mock implementations for Stripe webhook events and API responses.
 * Use these in tests to simulate Stripe interactions without making real API calls.
 */

import crypto from 'crypto';

/**
 * Generate a mock Stripe webhook signature
 *
 * This is critical for testing webhook signature verification.
 * Uses the same algorithm as Stripe's actual signature generation.
 *
 * @param payload - The raw request body
 * @param secret - The webhook secret (use test secret)
 * @param timestamp - Unix timestamp (optional, defaults to now)
 */
export function generateStripeSignature(
  payload: string,
  secret: string,
  timestamp?: number
): string {
  const ts = timestamp || Math.floor(Date.now() / 1000);
  const signedPayload = `${ts}.${payload}`;

  const signature = crypto
    .createHmac('sha256', secret)
    .update(signedPayload)
    .digest('hex');

  return `t=${ts},v1=${signature}`;
}

/**
 * Mock Stripe checkout session for successful purchase
 */
export const mockCheckoutSessionCompleted = {
  id: 'evt_test_123',
  object: 'event',
  type: 'checkout.session.completed',
  created: Math.floor(Date.now() / 1000),
  data: {
    object: {
      id: 'cs_test_mock123',
      object: 'checkout.session',
      amount_total: 7900,
      currency: 'usd',
      customer: 'cus_mock123',
      customer_email: 'customer@example.com',
      customer_details: {
        email: 'customer@example.com',
        name: 'Test Customer',
      },
      metadata: {
        user_id: 'user-123',
        product_id: 'prod_mock',
      },
      mode: 'payment',
      payment_status: 'paid',
      status: 'complete',
      success_url: 'https://example.com/success',
      cancel_url: 'https://example.com/cancel',
    },
  },
  livemode: false,
  pending_webhooks: 1,
  request: {
    id: 'req_test_123',
    idempotency_key: null,
  },
};

/**
 * Mock Stripe subscription created event
 */
export const mockSubscriptionCreated = {
  id: 'evt_test_sub_created',
  object: 'event',
  type: 'customer.subscription.created',
  created: Math.floor(Date.now() / 1000),
  data: {
    object: {
      id: 'sub_mock123',
      object: 'subscription',
      customer: 'cus_mock123',
      status: 'active',
      current_period_start: Math.floor(Date.now() / 1000),
      current_period_end: Math.floor(Date.now() / 1000) + 30 * 24 * 60 * 60,
      items: {
        data: [
          {
            id: 'si_mock123',
            price: {
              id: 'price_mock123',
              product: 'prod_mock123',
              unit_amount: 2900,
              currency: 'usd',
              recurring: {
                interval: 'month',
              },
            },
          },
        ],
      },
      metadata: {
        user_id: 'user-123',
      },
    },
  },
  livemode: false,
};

/**
 * Mock Stripe subscription updated event
 */
export const mockSubscriptionUpdated = {
  id: 'evt_test_sub_updated',
  object: 'event',
  type: 'customer.subscription.updated',
  created: Math.floor(Date.now() / 1000),
  data: {
    object: {
      id: 'sub_mock123',
      object: 'subscription',
      customer: 'cus_mock123',
      status: 'active',
      cancel_at_period_end: false,
      current_period_start: Math.floor(Date.now() / 1000),
      current_period_end: Math.floor(Date.now() / 1000) + 30 * 24 * 60 * 60,
      items: {
        data: [
          {
            id: 'si_mock123',
            price: {
              id: 'price_pro_mock',
              product: 'prod_pro_mock',
              unit_amount: 7900,
              currency: 'usd',
            },
          },
        ],
      },
    },
    previous_attributes: {
      items: {
        data: [
          {
            price: {
              id: 'price_starter_mock',
              unit_amount: 2900,
            },
          },
        ],
      },
    },
  },
  livemode: false,
};

/**
 * Mock Stripe subscription deleted/cancelled event
 */
export const mockSubscriptionDeleted = {
  id: 'evt_test_sub_deleted',
  object: 'event',
  type: 'customer.subscription.deleted',
  created: Math.floor(Date.now() / 1000),
  data: {
    object: {
      id: 'sub_mock123',
      object: 'subscription',
      customer: 'cus_mock123',
      status: 'canceled',
      canceled_at: Math.floor(Date.now() / 1000),
      metadata: {
        user_id: 'user-123',
      },
    },
  },
  livemode: false,
};

/**
 * Mock Stripe invoice paid event
 */
export const mockInvoicePaid = {
  id: 'evt_test_invoice_paid',
  object: 'event',
  type: 'invoice.paid',
  created: Math.floor(Date.now() / 1000),
  data: {
    object: {
      id: 'in_mock123',
      object: 'invoice',
      customer: 'cus_mock123',
      subscription: 'sub_mock123',
      amount_paid: 2900,
      currency: 'usd',
      status: 'paid',
      paid: true,
    },
  },
  livemode: false,
};

/**
 * Mock Stripe invoice payment failed event
 */
export const mockInvoicePaymentFailed = {
  id: 'evt_test_invoice_failed',
  object: 'event',
  type: 'invoice.payment_failed',
  created: Math.floor(Date.now() / 1000),
  data: {
    object: {
      id: 'in_mock123',
      object: 'invoice',
      customer: 'cus_mock123',
      subscription: 'sub_mock123',
      amount_due: 2900,
      currency: 'usd',
      status: 'open',
      paid: false,
      attempt_count: 1,
      next_payment_attempt: Math.floor(Date.now() / 1000) + 3 * 24 * 60 * 60,
    },
  },
  livemode: false,
};

/**
 * Create a mock Stripe client
 */
export function createMockStripeClient() {
  return {
    webhooks: {
      constructEvent: jest.fn((payload, sig, secret) => {
        // Return the parsed event for testing
        try {
          return JSON.parse(payload);
        } catch {
          throw new Error('Invalid payload');
        }
      }),
    },
    customers: {
      create: jest.fn().mockResolvedValue({ id: 'cus_new123' }),
      retrieve: jest.fn().mockResolvedValue({
        id: 'cus_mock123',
        email: 'customer@example.com',
      }),
      update: jest.fn().mockResolvedValue({ id: 'cus_mock123' }),
    },
    subscriptions: {
      create: jest.fn().mockResolvedValue({ id: 'sub_new123', status: 'active' }),
      retrieve: jest.fn().mockResolvedValue(mockSubscriptionCreated.data.object),
      update: jest.fn().mockResolvedValue({ id: 'sub_mock123' }),
      cancel: jest.fn().mockResolvedValue({ id: 'sub_mock123', status: 'canceled' }),
    },
    checkout: {
      sessions: {
        create: jest.fn().mockResolvedValue({
          id: 'cs_test_new123',
          url: 'https://checkout.stripe.com/pay/cs_test_new123',
        }),
        retrieve: jest.fn().mockResolvedValue(mockCheckoutSessionCompleted.data.object),
      },
    },
    products: {
      list: jest.fn().mockResolvedValue({
        data: [
          { id: 'prod_starter', name: 'Starter', active: true },
          { id: 'prod_pro', name: 'Pro', active: true },
        ],
      }),
    },
    prices: {
      list: jest.fn().mockResolvedValue({
        data: [
          { id: 'price_starter', product: 'prod_starter', unit_amount: 2900 },
          { id: 'price_pro', product: 'prod_pro', unit_amount: 7900 },
        ],
      }),
    },
  };
}

/**
 * Helper to create a complete webhook request for testing
 */
export function createWebhookRequest(
  event: Record<string, unknown>,
  secret: string
): { body: string; headers: Record<string, string> } {
  const body = JSON.stringify(event);
  const signature = generateStripeSignature(body, secret);

  return {
    body,
    headers: {
      'stripe-signature': signature,
      'content-type': 'application/json',
    },
  };
}
