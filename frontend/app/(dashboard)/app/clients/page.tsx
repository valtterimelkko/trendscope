'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, Users, TrendingUp, FileText } from 'lucide-react';

const MOCK_CLIENTS = [
  {
    id: '1',
    name: 'Fashion Brand Co.',
    logo: 'https://i.pravatar.cc/60?u=client1',
    niches: ['fashion', 'lifestyle'],
    trendCount: 24,
    lastReport: '2 days ago',
  },
  {
    id: '2',
    name: 'Beauty Startup',
    logo: 'https://i.pravatar.cc/60?u=client2',
    niches: ['beauty', 'wellness'],
    trendCount: 18,
    lastReport: '1 week ago',
  },
  {
    id: '3',
    name: 'Tech Company',
    logo: 'https://i.pravatar.cc/60?u=client3',
    niches: ['tech', 'business'],
    trendCount: 15,
    lastReport: '3 days ago',
  },
];

export default function ClientsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading-2 mb-2">Clients</h1>
          <p className="text-body text-muted-foreground">
            Manage client workspaces and trend tracking
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add Client
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Clients</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{MOCK_CLIENTS.length}</div>
            <p className="text-xs text-muted-foreground">Out of 5 available</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Trends</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">57</div>
            <p className="text-xs text-muted-foreground">Across all clients</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Reports Generated</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs text-muted-foreground">This month</p>
          </CardContent>
        </Card>
      </div>

      {/* Client List */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {MOCK_CLIENTS.map((client) => (
          <Card key={client.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <img
                    src={client.logo}
                    alt={client.name}
                    className="h-12 w-12 rounded-lg object-cover"
                  />
                  <div>
                    <CardTitle className="text-lg">{client.name}</CardTitle>
                    <CardDescription>
                      {client.niches.length} niches monitored
                    </CardDescription>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-1">
                {client.niches.map((niche) => (
                  <Badge key={niche} variant="secondary" className="text-xs">
                    #{niche}
                  </Badge>
                ))}
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Trends detected:</span>
                <span className="font-semibold">{client.trendCount}</span>
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Last report:</span>
                <span>{client.lastReport}</span>
              </div>

              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="flex-1" asChild>
                  <a href={`/app/clients/${client.id}`}>View Details</a>
                </Button>
                <Button size="sm" className="flex-1">
                  Generate Report
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
