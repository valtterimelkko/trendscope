'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';

export default function DangerZonePage() {
  const handleDeleteAccount = () => {
    if (confirm('Are you sure? This action cannot be undone.')) {
      console.log('Deleting account...');
    }
  };

  return (
    <div className="space-y-6">
      {/* Delete Account */}
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <div>
              <CardTitle className="text-red-600">Delete Account</CardTitle>
              <CardDescription>
                Permanently delete your account and all associated data
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-red-800">
            This action cannot be undone. All your data, trends, alerts, and client information will be permanently deleted.
          </p>
          <Button variant="destructive" onClick={handleDeleteAccount}>
            Delete My Account
          </Button>
        </CardContent>
      </Card>

      {/* Export Data */}
      <Card>
        <CardHeader>
          <CardTitle>Export Your Data</CardTitle>
          <CardDescription>
            Download a copy of your data
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Request a download of all your data in JSON format. This includes your trends, alerts, clients, and settings.
          </p>
          <Button variant="outline">
            Request Data Export
          </Button>
        </CardContent>
      </Card>

      {/* Log Out All Sessions */}
      <Card>
        <CardHeader>
          <CardTitle>Log Out All Sessions</CardTitle>
          <CardDescription>
            Sign out from all devices
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            This will log you out from all devices except this one.
          </p>
          <Button variant="outline">
            Log Out All Sessions
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
