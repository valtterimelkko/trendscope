'use client';

import { Button } from '@/components/ui/button';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { TrendCard } from '@/components/dashboard/TrendCard';
import { QuickActionsPanel } from '@/components/dashboard/QuickActionsPanel';
import { TrendFilterBar } from '@/components/dashboard/TrendFilterBar';
import { AlertItem } from '@/components/dashboard/AlertItem';
import { RecommendedActionsPanel } from '@/components/dashboard/RecommendedActionsPanel';
import { VelocityChart } from '@/components/dashboard/VelocityChart';
import { TrendingUp, Bell, Activity, Plus, Search } from 'lucide-react';
import { useState } from 'react';

// Mock data for velocity chart
const velocityChartData = [
  { time: '12 AM', velocity: 45 },
  { time: '4 AM', velocity: 52 },
  { time: '8 AM', velocity: 48 },
  { time: '12 PM', velocity: 65 },
  { time: '4 PM', velocity: 78 },
  { time: '8 PM', velocity: 89 },
];

export default function DashboardPage() {
  const [searchValue, setSearchValue] = useState('');
  const [nicheValue, setNicheValue] = useState('all');
  const [velocityValue, setVelocityValue] = useState('all');

  const handleQuickAction = (action: string) => {
    console.log(`Clicked: ${action}`);
  };

  return (
    <div className="space-y-6">
      {/* Header with CTAs */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-heading-2 mb-2">Welcome back, Sarah</h1>
          <p className="text-body text-muted-foreground">
            Here&apos;s your trend intelligence dashboard for today
          </p>
        </div>
        <div className="flex gap-3 w-full sm:w-auto">
          <Button variant="outline" className="flex-1 sm:flex-auto">
            <Search className="h-4 w-4 mr-2" />
            Search Trends
          </Button>
          <Button className="flex-1 sm:flex-auto">
            <Plus className="h-4 w-4 mr-2" />
            Create Alert
          </Button>
        </div>
      </div>

      {/* Stats Overview - 4 columns */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Active Trends"
          value="12"
          description="+3 from yesterday"
          icon={<TrendingUp className="h-4 w-4 text-primary" />}
        />
        <StatsCard
          title="Detected Today"
          value="3"
          description="6 hrs avg detection"
          icon={<Activity className="h-4 w-4 text-success" />}
        />
        <StatsCard
          title="Alerts Sent"
          value="28"
          description="This week"
          icon={<Bell className="h-4 w-4 text-accent" />}
        />
        <StatsCard
          title="Hit Rate"
          value="87%"
          description="+5% vs last week"
          icon={<TrendingUp className="h-4 w-4 text-success" />}
        />
      </div>

      {/* Quick Actions Panel */}
      <QuickActionsPanel
        actions={[
          { label: 'View All Trends', icon: '📊', onClick: () => handleQuickAction('Trends') },
          { label: 'Configure Alerts', icon: '🔔', onClick: () => handleQuickAction('Alerts') },
          { label: 'Manage Clients', icon: '👥', onClick: () => handleQuickAction('Clients') },
          { label: 'Export Report', icon: '📥', onClick: () => handleQuickAction('Export') },
        ]}
      />

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Trending Now - Takes 2 columns on lg */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-heading-3">🔥 Trending Now</h2>
            <Button variant="ghost" size="sm">↻ Refresh</Button>
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

          {/* Trend Cards */}
          <div className="space-y-3">
            <TrendCard
              name="Soft Glam Transformation"
              niche="beauty"
              velocity={89}
              videoCount="2,891"
              timeWindow="6 hours"
              onViewDetails={() => console.log('View Soft Glam')}
            />
            <TrendCard
              name="#QuietLuxury"
              niche="fashion"
              velocity={78}
              videoCount="1,234"
              timeWindow="12 hours"
              onViewDetails={() => console.log('View QuietLuxury')}
            />
            <TrendCard
              name="Finance Advice Format"
              niche="finance"
              velocity={65}
              videoCount="847"
              timeWindow="18 hours"
              onViewDetails={() => console.log('View Finance')}
            />
          </div>

          {/* Velocity Chart */}
          <div className="border rounded-lg p-6 bg-white">
            <h3 className="font-semibold mb-4">📈 Velocity Trend</h3>
            <VelocityChart data={velocityChartData} height={250} />
          </div>
        </div>

        {/* Activity Feed Sidebar - Takes 1 column */}
        <div className="space-y-4">
          {/* Recent Alerts */}
          <div className="border rounded-lg p-4 bg-white">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-heading-4">🔔 Recent Alerts</h2>
              <Button variant="ghost" size="sm" className="text-xs">View All</Button>
            </div>
            <div className="space-y-2">
              <AlertItem
                time="2h ago"
                message="Sound alert in #beauty"
                trend="Soft Glam Transformation"
                type="sound"
              />
              <AlertItem
                time="5h ago"
                message="Hashtag alert in #finance"
                trend="#MoneyTips"
                type="hashtag"
              />
              <AlertItem
                time="8h ago"
                message="Format alert in #fashion"
                trend="Get Ready With Me"
                type="format"
              />
            </div>
          </div>

          {/* Recommended Actions */}
          <RecommendedActionsPanel
            actions={[
              {
                title: '🎯 Set up niche alerts',
                description: 'Get instant notifications for beauty trends',
                icon: '🎯',
                buttonLabel: 'Configure',
                onClick: () => handleQuickAction('Config Alerts'),
              },
              {
                title: '📊 Export weekly report',
                description: 'Share insights with your team',
                icon: '📊',
                buttonLabel: 'Export',
                onClick: () => handleQuickAction('Export Report'),
              },
            ]}
          />
        </div>
      </div>
    </div>
  );
}
