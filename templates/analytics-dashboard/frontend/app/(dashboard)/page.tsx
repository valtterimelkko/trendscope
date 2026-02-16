import { Suspense } from 'react'
import { BigNumberCard } from '@/components/dashboard/BigNumberCard'
import { DateRangeController } from '@/components/dashboard/DateRangeController'
import { BreakdownList } from '@/components/dashboard/BreakdownList'
import { ActivityTicker } from '@/components/dashboard/ActivityTicker'
import { VisitorsChart } from '@/components/dashboard/VisitorsChart'

// Demo data - replace with real data fetching
const metrics = {
  visitors: { value: 12847, change: 12.5 },
  pageviews: { value: 34521, change: 8.2 },
  bounceRate: { value: 42.3, change: -3.1 },
  avgDuration: { value: '2m 34s', change: 15.7 },
}

const topSources = [
  { label: 'Google', value: 4521, percentage: 45 },
  { label: 'Direct', value: 2834, percentage: 28 },
  { label: 'Twitter', value: 1247, percentage: 12 },
  { label: 'LinkedIn', value: 892, percentage: 9 },
  { label: 'Other', value: 632, percentage: 6 },
]

const topPages = [
  { label: '/home', value: 8234, percentage: 52 },
  { label: '/pricing', value: 3421, percentage: 22 },
  { label: '/features', value: 2156, percentage: 14 },
  { label: '/blog', value: 1234, percentage: 8 },
  { label: '/about', value: 687, percentage: 4 },
]

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Header with Date Range */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-display font-bold">Dashboard</h1>
          <p className="text-foreground/70 text-sm mt-1">
            {/* CONTENT_SLOT: dashboard.subtitle */}
            Overview of your website analytics
          </p>
        </div>
        <DateRangeController />
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <BigNumberCard
          label="Visitors"
          value={metrics.visitors.value}
          change={metrics.visitors.change}
          format="number"
        />
        <BigNumberCard
          label="Pageviews"
          value={metrics.pageviews.value}
          change={metrics.pageviews.change}
          format="number"
        />
        <BigNumberCard
          label="Bounce Rate"
          value={metrics.bounceRate.value}
          change={metrics.bounceRate.change}
          format="percentage"
          invertColors
        />
        <BigNumberCard
          label="Avg. Duration"
          value={metrics.avgDuration.value}
          change={metrics.avgDuration.change}
          format="string"
        />
      </div>

      {/* Main Chart */}
      <div className="card p-6">
        <h2 className="font-semibold mb-4">Visitors Over Time</h2>
        <Suspense fallback={<div className="h-64 skeleton rounded-lg" />}>
          <VisitorsChart />
        </Suspense>
      </div>

      {/* Breakdowns Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Top Sources */}
        <div className="card p-6">
          <h2 className="font-semibold mb-4">Top Sources</h2>
          <BreakdownList items={topSources} />
        </div>

        {/* Top Pages */}
        <div className="card p-6">
          <h2 className="font-semibold mb-4">Top Pages</h2>
          <BreakdownList items={topPages} showFavicon={false} />
        </div>

        {/* Live Activity */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Live Activity</h2>
            <span className="badge badge-success">
              <span className="w-2 h-2 rounded-full bg-success mr-1.5 animate-pulse" />
              Live
            </span>
          </div>
          <Suspense fallback={<div className="space-y-3">{[...Array(5)].map((_, i) => <div key={i} className="h-12 skeleton rounded-lg" />)}</div>}>
            <ActivityTicker />
          </Suspense>
        </div>
      </div>
    </div>
  )
}
