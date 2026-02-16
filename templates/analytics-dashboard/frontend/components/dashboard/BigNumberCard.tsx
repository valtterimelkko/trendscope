'use client'

import { ArrowUp, ArrowDown } from 'lucide-react'
import { formatNumber, formatPercentage } from '@/lib/utils'

interface BigNumberCardProps {
  label: string
  value: number | string
  change: number
  format?: 'number' | 'percentage' | 'string'
  invertColors?: boolean
}

export function BigNumberCard({
  label,
  value,
  change,
  format = 'number',
  invertColors = false,
}: BigNumberCardProps) {
  const isPositive = invertColors ? change < 0 : change > 0
  const formattedValue =
    format === 'number'
      ? formatNumber(value as number)
      : format === 'percentage'
      ? `${value}%`
      : value

  return (
    <div className="big-number-card group hover:shadow-md transition-shadow">
      <p className="metric-label">{label}</p>
      <p className="metric-value mt-2">{formattedValue}</p>
      <div className="flex items-center gap-1 mt-2">
        {isPositive ? (
          <ArrowUp className="h-4 w-4 text-success" />
        ) : (
          <ArrowDown className="h-4 w-4 text-error" />
        )}
        <span className={`metric-change ${isPositive ? 'positive' : 'negative'}`}>
          {formatPercentage(change)}
        </span>
        <span className="text-xs text-foreground/50">vs last period</span>
      </div>

      {/* Sparkline background - placeholder */}
      <div className="absolute bottom-0 left-0 right-0 h-16 opacity-10 pointer-events-none">
        <svg
          viewBox="0 0 100 30"
          className="w-full h-full"
          preserveAspectRatio="none"
        >
          <path
            d="M0,25 Q25,10 50,20 T100,15"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className={isPositive ? 'text-success' : 'text-error'}
          />
        </svg>
      </div>
    </div>
  )
}
