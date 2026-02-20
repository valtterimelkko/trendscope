'use client';

import { Button } from '@/components/ui/button';
import { AlertItem } from '@/components/dashboard/AlertItem';
import { Card, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { TrendingUp, Bell, CheckCircle } from 'lucide-react';
import { useState } from 'react';

// Mock alerts data
const mockAlerts = [
  {
    id: '1',
    type: 'sound',
    message: 'Sound alert in #beauty',
    trend: 'Soft Glam Transformation',
    time: '2h ago',
  },
  {
    id: '2',
    type: 'hashtag',
    message: 'Hashtag alert in #finance',
    trend: '#MoneyTips',
    time: '5h ago',
  },
  {
    id: '3',
    type: 'format',
    message: 'Format alert in #fashion',
    trend: 'Get Ready With Me',
    time: '8h ago',
  },
  {
    id: '4',
    type: 'sound',
    message: 'Sound alert in #lifestyle',
    trend: 'Morning Routine',
    time: '12h ago',
  },
  {
    id: '5',
    type: 'hashtag',
    message: 'Hashtag alert in #tech',
    trend: '#AIBreakthrough',
    time: '1d ago',
  },
];

export default function AlertsPage() {
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const stats = [
    { title: 'Total Alerts', value: '156', icon: <Bell className="h-4 w-4 text-accent" /> },
    { title: 'This Week', value: '28', icon: <TrendingUp className="h-4 w-4 text-primary" /> },
    {
      title: 'Processed',
      value: '142',
      icon: <CheckCircle className="h-4 w-4 text-success" />,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-heading-2 mb-2">Alerts</h1>
        <p className="text-body text-muted-foreground">
          Manage your trend alerts and notifications
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
        {stats.map((stat, idx) => (
          <Card key={idx}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-caption">{stat.title}</p>
                  <p className="text-stat-value">{stat.value}</p>
                </div>
                {stat.icon}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filter Bar */}
      <div className="flex gap-3 flex-col sm:flex-row">
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="All Types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="sound">Sound Alerts</SelectItem>
            <SelectItem value="hashtag">Hashtag Alerts</SelectItem>
            <SelectItem value="format">Format Alerts</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="dismissed">Dismissed</SelectItem>
            <SelectItem value="snoozed">Snoozed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Alerts List */}
      <div className="space-y-2">
        {mockAlerts.map((alert) => (
          <AlertItem
            key={alert.id}
            time={alert.time}
            message={alert.message}
            trend={alert.trend}
            type={alert.type as 'sound' | 'hashtag' | 'format'}
          />
        ))}
      </div>

      {/* Load More */}
      <div className="text-center pt-6">
        <Button variant="outline" size="lg">
          Load More Alerts
        </Button>
      </div>
    </div>
  );
}
