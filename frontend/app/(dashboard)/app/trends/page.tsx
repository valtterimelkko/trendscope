'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { EmptyState } from '@/components/common/EmptyState';
import { Filter, TrendingUp } from 'lucide-react';
import { useState } from 'react';

export default function TrendsPage() {
  const [niche, setNiche] = useState<string>('all');
  const [status, setStatus] = useState<string>('all');

  // Mock data - will be replaced with real API call
  const trends = [
    {
      id: '1',
      name: 'Soft Glam Transformation',
      type: 'sound',
      niche: 'beauty',
      velocity: 89,
      saturation: 12,
      videoCount: 2891,
      timeWindow: '6-8 hours',
      status: 'emerging',
    },
    {
      id: '2',
      name: '#QuietLuxury',
      type: 'hashtag',
      niche: 'fashion',
      velocity: 78,
      saturation: 25,
      videoCount: 1234,
      timeWindow: '12 hours',
      status: 'peaking',
    },
    {
      id: '3',
      name: 'Finance Advice Format',
      type: 'format',
      niche: 'finance',
      velocity: 65,
      saturation: 45,
      videoCount: 847,
      timeWindow: '18 hours',
      status: 'peaking',
    },
  ];

  const filteredTrends = trends.filter((trend) => {
    if (niche !== 'all' && trend.niche !== niche) return false;
    if (status !== 'all' && trend.status !== status) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading-2 mb-2">Trends</h1>
          <p className="text-body text-muted-foreground">
            Discover emerging trends before they peak
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <Select value={niche} onValueChange={setNiche}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select niche" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Niches</SelectItem>
            <SelectItem value="beauty">Beauty</SelectItem>
            <SelectItem value="fashion">Fashion</SelectItem>
            <SelectItem value="finance">Finance</SelectItem>
            <SelectItem value="gaming">Gaming</SelectItem>
          </SelectContent>
        </Select>

        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="emerging">Emerging</SelectItem>
            <SelectItem value="peaking">Peaking</SelectItem>
            <SelectItem value="declining">Declining</SelectItem>
          </SelectContent>
        </Select>

        <Button variant="outline" className="ml-auto">
          <Filter className="mr-2 h-4 w-4" />
          More Filters
        </Button>
      </div>

      {/* Trends List */}
      {filteredTrends.length === 0 ? (
        <EmptyState
          title="No trends found"
          description="Try adjusting your filters or check back later for new trends."
          icon="📊"
        />
      ) : (
        <div className="grid gap-4">
          {filteredTrends.map((trend) => (
            <TrendListItem key={trend.id} trend={trend} />
          ))}
        </div>
      )}
    </div>
  );
}

function TrendListItem({ trend }: { trend: any }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'emerging':
        return 'bg-green-100 text-green-800';
      case 'peaking':
        return 'bg-yellow-100 text-yellow-800';
      case 'declining':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getVelocityColor = (score: number) => {
    if (score >= 70) return 'bg-green-500';
    if (score >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getSaturationColor = (percentage: number) => {
    if (percentage < 30) return 'text-green-600';
    if (percentage < 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <a href={`/app/trends/${trend.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardContent className="p-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 space-y-3">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold">{trend.name}</h3>
                <Badge className={getStatusColor(trend.status)}>
                  {trend.status}
                </Badge>
                <Badge variant="outline">{trend.type}</Badge>
              </div>

              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Badge variant="secondary" className="text-xs">
                    {trend.niche}
                  </Badge>
                </span>
                <span>{trend.videoCount.toLocaleString()} videos</span>
                <span>⏰ {trend.timeWindow} window</span>
              </div>

              {/* Velocity Bar */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Velocity</span>
                  <span className="font-medium">+{trend.velocity}%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getVelocityColor(trend.velocity)} transition-all`}
                    style={{ width: `${trend.velocity}%` }}
                  />
                </div>
              </div>

              {/* Saturation */}
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Saturation</span>
                <span className={`font-medium ${getSaturationColor(trend.saturation)}`}>
                  {trend.saturation}%
                </span>
              </div>
            </div>

            <div className="flex flex-col items-end justify-between h-full">
              <TrendingUp className="h-8 w-8 text-primary" />
              <Button variant="outline" size="sm">
                View Details
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </a>
  );
}
