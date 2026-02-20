'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export default function BillingPage() {
  return (
    <div className="space-y-6">
      {/* Current Plan */}
      <Card>
        <CardHeader>
          <CardTitle>Current Plan</CardTitle>
          <CardDescription>
            You are on the Pro plan
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between pb-4 border-b">
            <div>
              <h4 className="font-semibold mb-2">Pro Plan</h4>
              <p className="text-sm text-muted-foreground">$99/month</p>
            </div>
            <Badge>Active</Badge>
          </div>

          <div>
            <h4 className="font-semibold mb-3">Plan Features:</h4>
            <ul className="space-y-2 text-sm">
              <li>✓ Unlimited trend monitoring</li>
              <li>✓ 100 custom alerts</li>
              <li>✓ Advanced analytics</li>
              <li>✓ Team collaboration (up to 5 users)</li>
              <li>✓ Priority support</li>
            </ul>
          </div>

          <div className="flex gap-3 pt-4">
            <Button variant="outline">Change Plan</Button>
            <Button variant="outline">Cancel Subscription</Button>
          </div>
        </CardContent>
      </Card>

      {/* Billing History */}
      <Card>
        <CardHeader>
          <CardTitle>Billing History</CardTitle>
          <CardDescription>
            Your recent invoices and payments
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { date: 'Feb 20, 2026', amount: '$99.00', status: 'Paid' },
              { date: 'Jan 20, 2026', amount: '$99.00', status: 'Paid' },
              { date: 'Dec 20, 2025', amount: '$99.00', status: 'Paid' },
            ].map(invoice => (
              <div key={invoice.date} className="flex items-center justify-between py-3 border-b last:border-b-0">
                <div>
                  <p className="font-medium">{invoice.date}</p>
                  <p className="text-sm text-muted-foreground">{invoice.amount}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant="outline">{invoice.status}</Badge>
                  <Button variant="ghost" size="sm">Download</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Payment Method */}
      <Card>
        <CardHeader>
          <CardTitle>Payment Method</CardTitle>
          <CardDescription>
            Update your payment information
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 border rounded-lg bg-surface">
            <p className="font-medium">💳 Visa ending in 4242</p>
            <p className="text-sm text-muted-foreground">Expires 12/2026</p>
          </div>
          <Button variant="outline">Update Payment Method</Button>
        </CardContent>
      </Card>
    </div>
  );
}
