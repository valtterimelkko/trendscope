'use client';

import { Button } from '@/components/ui/button';
import { TrendCard } from '@/components/dashboard/TrendCard';
import { TrendFilterBar } from '@/components/dashboard/TrendFilterBar';
import { useState } from 'react';
import { Plus } from 'lucide-react';

// Mock data
const mockTrends = [
  {
    id: '1',
    name: 'Soft Glam Transformation',
    niche: 'beauty',
    velocity: 89,
    videoCount: '2,891',
    timeWindow: '6 hours',
  },
  {
    id: '2',
    name: '#QuietLuxury',
    niche: 'fashion',
    velocity: 78,
    videoCount: '1,234',
    timeWindow: '12 hours',
  },
  {
    id: '3',
    name: 'Finance Advice Format',
    niche: 'finance',
    velocity: 65,
    videoCount: '847',
    timeWindow: '18 hours',
  },
  {
    id: '4',
    name: 'Clean Girl Aesthetic',
    niche: 'beauty',
    velocity: 74,
    videoCount: '2,156',
    timeWindow: '8 hours',
  },
  {
    id: '5',
    name: 'Sustainable Fashion',
    niche: 'fashion',
    velocity: 52,
    videoCount: '891',
    timeWindow: '24 hours',
  },
];

export default function TrendsPage() {
  const [searchValue, setSearchValue] = useState('');
  const [nicheValue, setNicheValue] = useState('all');
  const [velocityValue, setVelocityValue] = useState('all');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-heading-2 mb-2">Discover Trends</h1>
          <p className="text-body text-muted-foreground">
            Explore emerging trends across all niches
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Add to Watchlist
        </Button>
      </div>

      {/* Filter Bar */}
      <TrendFilterBar
        searchValue={searchValue}
        nicheValue={nicheValue}
        velocityValue={velocityValue}
        onSearchChange={setSearchValue}
        onNicheChange={setNicheValue}
        onVelocityChange={setVelocityValue}
      />

      {/* Trends Grid */}
      <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
        {mockTrends.map((trend) => (
          <TrendCard
            key={trend.id}
            name={trend.name}
            niche={trend.niche}
            velocity={trend.velocity}
            videoCount={trend.videoCount}
            timeWindow={trend.timeWindow}
            onViewDetails={() => console.log(`View ${trend.name}`)}
            onBookmark={() => console.log(`Bookmark ${trend.name}`)}
          />
        ))}
      </div>

      {/* Load More */}
      <div className="text-center pt-6">
        <Button variant="outline" size="lg">
          Load More Trends
        </Button>
      </div>
    </div>
  );
}
