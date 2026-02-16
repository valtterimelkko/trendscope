'use client'

import { useMemo } from 'react'

interface UsageGaugeProps {
  current: number
  limit: number
  unit: string
  renewsAt?: Date
  showPercentage?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function UsageGauge({
  current,
  limit,
  unit,
  renewsAt,
  showPercentage = true,
  size = 'md',
}: UsageGaugeProps) {
  const percentage = useMemo(() => {
    if (limit === -1) return 0 // Unlimited
    return Math.min((current / limit) * 100, 100)
  }, [current, limit])

  const colorClass = useMemo(() => {
    if (limit === -1) return 'bg-green-500' // Unlimited
    if (percentage >= 90) return 'bg-red-500'
    if (percentage >= 75) return 'bg-yellow-500'
    return 'bg-green-500'
  }, [percentage, limit])

  const textColorClass = useMemo(() => {
    if (limit === -1) return 'text-green-600'
    if (percentage >= 90) return 'text-red-600'
    if (percentage >= 75) return 'text-yellow-600'
    return 'text-green-600'
  }, [percentage, limit])

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  const daysUntilRenewal = useMemo(() => {
    if (!renewsAt) return null
    const now = new Date()
    const diff = renewsAt.getTime() - now.getTime()
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)))
  }, [renewsAt])

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {limit === -1 ? (
            <>Unlimited {unit}s</>
          ) : (
            <>
              <span className={textColorClass}>{formatNumber(current)}</span>
              <span className="text-gray-400"> / {formatNumber(limit)} {unit}s</span>
            </>
          )}
        </span>
        {showPercentage && limit !== -1 && (
          <span className={`text-sm font-medium ${textColorClass}`}>
            {percentage.toFixed(0)}%
          </span>
        )}
      </div>

      <div className={`w-full bg-gray-200 dark:bg-gray-700 rounded-full ${sizeClasses[size]}`}>
        <div
          className={`${colorClass} ${sizeClasses[size]} rounded-full transition-all duration-300`}
          style={{ width: limit === -1 ? '100%' : `${percentage}%` }}
        />
      </div>

      {daysUntilRenewal !== null && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Resets in {daysUntilRenewal} day{daysUntilRenewal !== 1 ? 's' : ''}
        </p>
      )}

      {limit !== -1 && percentage >= 90 && (
        <p className="text-xs text-red-600 dark:text-red-400 mt-1 font-medium">
          Approaching limit! Upgrade for more {unit}s.
        </p>
      )}
    </div>
  )
}
