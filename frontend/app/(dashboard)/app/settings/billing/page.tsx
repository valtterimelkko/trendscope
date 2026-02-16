'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2 } from 'lucide-react';

const PRICING_TIERS = [
  {
    name: 'Free',
    price: '$0',
    period: '',
    features: [
      'Weekly digest (7 trends max)',
      '1 niche',
      'Email delivery',
      'Basic trend data',
    ],
    current: false,
  },
  {
    name: 'Solo',
    price: '$29',
    period: '/month',
    features: [
      '2-hour alert latency',
      'Unlimited niches',
      'Slack integration',
      'Saturation tracking',
      'Velocity scores',
      'Unlimited alerts',
    ],
    current: true,
  },
  {
    name: 'Agency',
    price: '$199',
    period: '/month',
    features: [
      '30-minute alert latency',
      '5 client workspaces',
      'White-label reports',
      '12 monitored niches',
      'API access',
      'Priority support',
    ],
    current: false,
  },
];

export default function BillingSettingsPage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Current Plan</CardTitle>
          <CardDescription>
            You&apos;re currently on the Solo plan
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between rounded-lg border-2 border-primary bg-primary/5 p-4">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-bold">Solo</h3>
                <Badge>Active</Badge>
              </div>
              <p className="text-2xl font-bold text-primary mt-2">$29/month</p>
              <p className="text-sm text-muted-foreground mt-1">
                Next billing date: March 16, 2026
              </p>
            </div>
            <Button variant="outline">Manage Subscription</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Upgrade Your Plan</CardTitle>
          <CardDescription>
            Choose a plan that fits your needs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-3">
            {PRICING_TIERS.map((tier) => (
              <div
                key={tier.name}
                className={`rounded-lg border-2 p-6 ${
                  tier.current ? 'border-primary' : 'border-gray-200'
                }`}
              >
                <div className="mb-4">
                  <h3 className="text-lg font-bold">{tier.name}</h3>
                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="text-3xl font-bold">{tier.price}</span>
                    <span className="text-muted-foreground">{tier.period}</span>
                  </div>
                </div>
                <ul className="space-y-2 mb-6">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm">
                      <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                {tier.current ? (
                  <Button variant="outline" className="w-full" disabled>
                    Current Plan
                  </Button>
                ) : (
                  <Button className="w-full">
                    {tier.price === '$0' ? 'Downgrade' : 'Upgrade'}
                  </Button>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Payment Method</CardTitle>
          <CardDescription>
            Manage your billing information
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div>
              <p className="font-medium">•••• •••• •••• 4242</p>
              <p className="text-sm text-muted-foreground">Expires 12/2026</p>
            </div>
            <Button variant="outline" size="sm">
              Update
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Invoice History</CardTitle>
          <CardDescription>
            Download past invoices
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[
              { date: 'Feb 16, 2026', amount: '$29.00', status: 'Paid' },
              { date: 'Jan 16, 2026', amount: '$29.00', status: 'Paid' },
              { date: 'Dec 16, 2025', amount: '$29.00', status: 'Paid' },
            ].map((invoice) => (
              <div
                key={invoice.date}
                className="flex items-center justify-between rounded-lg border p-3"
              >
                <div className="flex items-center gap-4">
                  <div>
                    <p className="font-medium">{invoice.date}</p>
                    <p className="text-sm text-muted-foreground">{invoice.amount}</p>
                  </div>
                  <Badge variant="outline">{invoice.status}</Badge>
                </div>
                <Button variant="ghost" size="sm">
                  Download
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
