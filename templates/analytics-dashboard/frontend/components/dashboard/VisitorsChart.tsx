'use client'

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

// Demo data - replace with real data
const data = [
  { date: 'Mon', visitors: 1200, pageviews: 2400 },
  { date: 'Tue', visitors: 1890, pageviews: 3200 },
  { date: 'Wed', visitors: 2390, pageviews: 4100 },
  { date: 'Thu', visitors: 1490, pageviews: 2800 },
  { date: 'Fri', visitors: 2490, pageviews: 4300 },
  { date: 'Sat', visitors: 2190, pageviews: 3900 },
  { date: 'Sun', visitors: 1890, pageviews: 3400 },
]

export function VisitorsChart() {
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorVisitors" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.2} />
              <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--color-border)"
            vertical={false}
          />
          <XAxis
            dataKey="date"
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
            tickFormatter={(value) =>
              value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value
            }
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--color-background)',
              border: '1px solid var(--color-border)',
              borderRadius: '8px',
              boxShadow: 'var(--shadow-md)',
            }}
            labelStyle={{ color: 'var(--color-text-primary)', fontWeight: 600 }}
            itemStyle={{ color: 'var(--color-text-secondary)' }}
          />
          <Area
            type="monotone"
            dataKey="visitors"
            stroke="var(--color-primary)"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorVisitors)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
