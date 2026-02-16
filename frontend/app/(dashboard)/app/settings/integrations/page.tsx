'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { CheckCircle2, XCircle } from 'lucide-react';

export default function IntegrationsSettingsPage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Slack Integration</CardTitle>
              <CardDescription>
                Receive trend alerts directly in your Slack workspace
              </CardDescription>
            </div>
            <Badge variant="outline" className="gap-1">
              <CheckCircle2 className="h-3 w-3 text-green-600" />
              Connected
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="webhookUrl">Webhook URL</Label>
            <Input
              id="webhookUrl"
              placeholder="https://hooks.slack.com/services/..."
              defaultValue="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
            />
            <p className="text-xs text-muted-foreground">
              Get your webhook URL from{' '}
              <a
                href="https://api.slack.com/messaging/webhooks"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                Slack&apos;s API settings
              </a>
            </p>
          </div>

          <div className="flex items-center justify-between rounded-lg border p-4">
            <div>
              <p className="font-medium">Enable Slack Alerts</p>
              <p className="text-sm text-muted-foreground">
                Send trend alerts to your Slack channel
              </p>
            </div>
            <Switch defaultChecked />
          </div>

          <div className="flex gap-3">
            <Button variant="outline">Test Connection</Button>
            <Button>Save Changes</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Email Notifications</CardTitle>
              <CardDescription>
                Configure email alert preferences
              </CardDescription>
            </div>
            <Badge variant="outline" className="gap-1">
              <CheckCircle2 className="h-3 w-3 text-green-600" />
              Active
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-lg border p-4">
              <div>
                <p className="font-medium">Instant Alerts</p>
                <p className="text-sm text-muted-foreground">
                  Real-time email notifications for new trends
                </p>
              </div>
              <Switch defaultChecked />
            </div>

            <div className="flex items-center justify-between rounded-lg border p-4">
              <div>
                <p className="font-medium">Daily Digest</p>
                <p className="text-sm text-muted-foreground">
                  Daily summary of detected trends
                </p>
              </div>
              <Switch />
            </div>

            <div className="flex items-center justify-between rounded-lg border p-4">
              <div>
                <p className="font-medium">Weekly Report</p>
                <p className="text-sm text-muted-foreground">
                  Weekly trend intelligence report
                </p>
              </div>
              <Switch defaultChecked />
            </div>
          </div>

          <div className="flex justify-end">
            <Button>Save Preferences</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>SMS Alerts</CardTitle>
              <CardDescription>
                Get urgent trend alerts via text message
              </CardDescription>
            </div>
            <Badge variant="secondary">Agency Tier</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            SMS alerts are available on Agency and Enterprise plans.
          </p>
          <Button variant="outline" asChild>
            <a href="/app/settings/billing">Upgrade Plan</a>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
