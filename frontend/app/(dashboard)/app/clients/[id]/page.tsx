'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, Download, Share2, Settings } from 'lucide-react';
import { use } from 'react';
import Link from 'next/link';

export default function ClientDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  // Mock client data
  const client = {
    id,
    name: 'Fashion Brand Co.',
    logo: 'https://i.pravatar.cc/80?u=client1',
    niches: ['fashion', 'lifestyle', 'beauty'],
    alertDestination: 'client-trends@fashionbrand.com',
    createdAt: 'Jan 15, 2026',
    trendCount: 24,
  };

  const recentTrends = [
    { id: '1', name: '#QuietLuxury', velocity: 78, saturation: 25, detectedAt: '2 days ago' },
    { id: '2', name: 'Minimalist OOTD', velocity: 65, saturation: 18, detectedAt: '4 days ago' },
    { id: '3', name: 'Capsule Wardrobe', velocity: 72, saturation: 32, detectedAt: '6 days ago' },
  ];

  return (
    <div className="space-y-6">
      <Button variant="ghost" asChild>
        <Link href="/app/clients" className="flex items-center gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back to Clients
        </Link>
      </Button>

      {/* Client Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <img
            src={client.logo}
            alt={client.name}
            className="h-16 w-16 rounded-lg object-cover"
          />
          <div>
            <h1 className="text-heading-2">{client.name}</h1>
            <p className="text-body-sm text-muted-foreground">
              Client since {client.createdAt}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon">
            <Settings className="h-4 w-4" />
          </Button>
          <Button>
            <Download className="mr-2 h-4 w-4" />
            Generate Report
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Monitored Niches</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{client.niches.length}</div>
            <div className="mt-2 flex flex-wrap gap-1">
              {client.niches.map((niche) => (
                <Badge key={niche} variant="secondary" className="text-xs">
                  #{niche}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Trends Detected</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{client.trendCount}</div>
            <p className="text-xs text-muted-foreground">Total since creation</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Alert Destination</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">{client.alertDestination}</div>
            <p className="text-xs text-muted-foreground">Email delivery</p>
          </CardContent>
        </Card>
      </div>

      {/* Client Workspace */}
      <Tabs defaultValue="trends" className="space-y-4">
        <TabsList>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="trends">
          <Card>
            <CardHeader>
              <CardTitle>Recent Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentTrends.map((trend) => (
                  <div
                    key={trend.id}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >
                    <div className="flex-1">
                      <h3 className="font-semibold">{trend.name}</h3>
                      <p className="text-sm text-muted-foreground">
                        Detected {trend.detectedAt}
                      </p>
                    </div>
                    <div className="flex items-center gap-6 text-sm">
                      <div>
                        <span className="text-muted-foreground">Velocity: </span>
                        <span className="font-semibold text-primary">{trend.velocity}%</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Saturation: </span>
                        <span className="font-semibold">{trend.saturation}%</span>
                      </div>
                      <Button variant="ghost" size="sm">
                        View
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reports">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Generated Reports</CardTitle>
                <Button>
                  <Download className="mr-2 h-4 w-4" />
                  New Report
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { date: 'Feb 10, 2026', trends: 12, format: 'PDF' },
                  { date: 'Feb 3, 2026', trends: 8, format: 'PDF' },
                  { date: 'Jan 27, 2026', trends: 15, format: 'PDF' },
                ].map((report) => (
                  <div
                    key={report.date}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >
                    <div>
                      <p className="font-medium">Weekly Trend Report</p>
                      <p className="text-sm text-muted-foreground">
                        {report.date} • {report.trends} trends • {report.format}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm">
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Share2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>Client Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Client configuration options will be here.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
