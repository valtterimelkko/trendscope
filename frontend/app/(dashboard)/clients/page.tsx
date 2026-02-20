'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Plus, Search, MoreVertical } from 'lucide-react';
import { useState } from 'react';

// Mock clients data
const mockClients = [
  {
    id: '1',
    name: 'Acme Beauty Co',
    email: 'hello@acmebeauty.com',
    initials: 'AB',
    monitoringStatus: 'active',
    trendsTracked: 12,
  },
  {
    id: '2',
    name: 'Fashion Forward LLC',
    email: 'contact@fashionforward.com',
    initials: 'FF',
    monitoringStatus: 'active',
    trendsTracked: 8,
  },
  {
    id: '3',
    name: 'Tech Innovations Inc',
    email: 'hello@techinnovations.com',
    initials: 'TI',
    monitoringStatus: 'inactive',
    trendsTracked: 0,
  },
  {
    id: '4',
    name: 'Lifestyle Brands Co',
    email: 'contact@lifestylebrand.com',
    initials: 'LB',
    monitoringStatus: 'active',
    trendsTracked: 15,
  },
];

export default function ClientsPage() {
  const [searchValue, setSearchValue] = useState('');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-heading-2 mb-2">Clients</h1>
          <p className="text-body text-muted-foreground">
            Manage your agency clients and their trend monitoring
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Add Client
        </Button>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search clients..."
          className="pl-10"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
        />
      </div>

      {/* Clients Grid */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
        {mockClients.map((client) => (
          <Card key={client.id} className="trend-card">
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3">
                  <Avatar>
                    <AvatarFallback>{client.initials}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <h3 className="font-semibold">{client.name}</h3>
                    <p className="text-caption">{client.email}</p>
                  </div>
                </div>
                <Button variant="ghost" size="sm">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-caption">Monitoring Status</p>
                  <Badge
                    variant={client.monitoringStatus === 'active' ? 'default' : 'outline'}
                  >
                    {client.monitoringStatus === 'active' ? '🟢 Active' : '🔴 Inactive'}
                  </Badge>
                </div>
                <div className="space-y-1 text-right">
                  <p className="text-caption">Trends Tracked</p>
                  <p className="text-stat-value">{client.trendsTracked}</p>
                </div>
              </div>

              <div className="mt-4 flex gap-2">
                <Button variant="outline" size="sm" className="flex-1">
                  View Details
                </Button>
                <Button variant="ghost" size="sm">
                  📊
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Load More */}
      <div className="text-center pt-6">
        <Button variant="outline" size="lg">
          Load More Clients
        </Button>
      </div>
    </div>
  );
}
