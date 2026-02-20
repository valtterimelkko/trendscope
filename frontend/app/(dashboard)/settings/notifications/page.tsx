'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

interface NotificationSetting {
  id: string;
  title: string;
  description: string;
  enabled: boolean;
}

export default function NotificationsPage() {
  const [settings, setSettings] = useState<NotificationSetting[]>([
    {
      id: 'trend-alerts',
      title: 'Trend Alerts',
      description: 'Get notified when new trends match your criteria',
      enabled: true,
    },
    {
      id: 'velocity-spikes',
      title: 'Velocity Spikes',
      description: 'Alert when trend velocity increases significantly',
      enabled: true,
    },
    {
      id: 'weekly-digest',
      title: 'Weekly Digest',
      description: 'Receive a summary of trends from the past week',
      enabled: false,
    },
    {
      id: 'client-alerts',
      title: 'Client Alerts',
      description: 'Notify when client trends are detected',
      enabled: true,
    },
    {
      id: 'system-updates',
      title: 'System Updates',
      description: 'Get notified about new features and updates',
      enabled: true,
    },
  ]);

  const handleToggle = (id: string) => {
    setSettings(prev =>
      prev.map(setting =>
        setting.id === id ? { ...setting, enabled: !setting.enabled } : setting
      )
    );
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Notification Preferences</CardTitle>
          <CardDescription>
            Choose how you want to be notified
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {settings.map(setting => (
            <div key={setting.id} className="flex items-center justify-between py-4 border-b last:border-b-0">
              <div className="flex-1">
                <h4 className="font-medium">{setting.title}</h4>
                <p className="text-sm text-muted-foreground">{setting.description}</p>
              </div>
              <Switch
                checked={setting.enabled}
                onCheckedChange={() => handleToggle(setting.id)}
              />
            </div>
          ))}

          <Button className="mt-6">Save Preferences</Button>
        </CardContent>
      </Card>

      {/* Email Preferences */}
      <Card>
        <CardHeader>
          <CardTitle>Email Frequency</CardTitle>
          <CardDescription>
            Choose how often you receive email notifications
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            {['Immediate', 'Daily Digest', 'Weekly Summary'].map(freq => (
              <div key={freq} className="flex items-center gap-3">
                <input type="radio" id={freq} name="frequency" defaultChecked={freq === 'Immediate'} />
                <label htmlFor={freq} className="text-sm">{freq}</label>
              </div>
            ))}
          </div>
          <Button>Save</Button>
        </CardContent>
      </Card>
    </div>
  );
}
