'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface Integration {
  name: string;
  description: string;
  status: 'connected' | 'disconnected';
  icon: string;
}

const integrations: Integration[] = [
  {
    name: 'Slack',
    description: 'Get trend alerts in your Slack channels',
    status: 'connected',
    icon: '💬',
  },
  {
    name: 'Discord',
    description: 'Receive notifications in Discord servers',
    status: 'disconnected',
    icon: '🎮',
  },
  {
    name: 'Zapier',
    description: 'Integrate with 5000+ apps via Zapier',
    status: 'disconnected',
    icon: '⚡',
  },
  {
    name: 'Google Sheets',
    description: 'Export trends automatically to Google Sheets',
    status: 'connected',
    icon: '📊',
  },
];

export default function IntegrationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-heading-4 mb-2">Connected Integrations</h2>
        <p className="text-body-sm text-muted-foreground">
          Manage third-party integrations
        </p>
      </div>

      <div className="grid gap-4">
        {integrations.map(integration => (
          <Card key={integration.name}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="text-4xl">{integration.icon}</div>
                  <div>
                    <h4 className="font-semibold">{integration.name}</h4>
                    <p className="text-sm text-muted-foreground">{integration.description}</p>
                  </div>
                </div>
                <div className="text-right space-y-3">
                  <Badge variant={integration.status === 'connected' ? 'default' : 'outline'}>
                    {integration.status === 'connected' ? '🟢 Connected' : '⚪ Disconnected'}
                  </Badge>
                  <div>
                    <Button size="sm" variant={integration.status === 'connected' ? 'outline' : 'default'}>
                      {integration.status === 'connected' ? 'Manage' : 'Connect'}
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
