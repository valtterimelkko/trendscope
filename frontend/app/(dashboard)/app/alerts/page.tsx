'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Bell, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { useState } from 'react';

// Mock alerts data
const MOCK_ALERTS = [
  {
    id: '1',
    trendName: 'Soft Glam Transformation',
    type: 'sound',
    niche: 'beauty',
    sentAt: '2 hours ago',
    channel: 'slack',
    status: 'sent',
    clicked: true,
  },
  {
    id: '2',
    trendName: '#QuietLuxury',
    type: 'hashtag',
    niche: 'fashion',
    sentAt: '5 hours ago',
    channel: 'email',
    status: 'sent',
    clicked: true,
  },
  {
    id: '3',
    trendName: 'Finance Advice Format',
    type: 'format',
    niche: 'finance',
    sentAt: '8 hours ago',
    channel: 'slack',
    status: 'sent',
    clicked: false,
  },
  {
    id: '4',
    trendName: 'Workout Transition',
    type: 'format',
    niche: 'fitness',
    sentAt: '12 hours ago',
    channel: 'slack',
    status: 'failed',
    clicked: false,
  },
];

export default function AlertsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filteredAlerts = MOCK_ALERTS.filter(
    (alert) => statusFilter === 'all' || alert.status === statusFilter
  );

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'sent':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'sent':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading-2 mb-2">Alerts</h1>
          <p className="text-body text-muted-foreground">
            View and manage your trend alert history
          </p>
        </div>
        <Button asChild>
          <a href="/app/settings/integrations">Configure Alerts</a>
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Alerts</CardTitle>
            <Bell className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">128</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">This Week</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">28</div>
            <p className="text-xs text-muted-foreground">+12% from last week</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Click-Through</CardTitle>
            <Clock className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">42%</div>
            <p className="text-xs text-muted-foreground">Alert engagement rate</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2</div>
            <p className="text-xs text-muted-foreground">Connection issues</p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Alert History</CardTitle>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="sent">Sent</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Trend</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Niche</TableHead>
                <TableHead>Channel</TableHead>
                <TableHead>Time</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAlerts.map((alert) => (
                <TableRow key={alert.id}>
                  <TableCell className="font-medium">{alert.trendName}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{alert.type}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary">#{alert.niche}</Badge>
                  </TableCell>
                  <TableCell className="capitalize">{alert.channel}</TableCell>
                  <TableCell className="text-muted-foreground">{alert.sentAt}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(alert.status)}
                      <Badge className={getStatusBadge(alert.status)}>
                        {alert.status}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell>
                    {alert.status === 'sent' && (
                      <Button variant="ghost" size="sm" asChild>
                        <a href={`/app/trends/${alert.id}`}>View Trend</a>
                      </Button>
                    )}
                    {alert.status === 'failed' && (
                      <Button variant="ghost" size="sm">
                        Retry
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
