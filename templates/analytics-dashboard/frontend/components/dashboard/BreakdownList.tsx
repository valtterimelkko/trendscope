'use client'

import { formatNumber } from '@/lib/utils'

interface BreakdownItem {
  label: string
  value: number
  percentage: number
  icon?: string
}

interface BreakdownListProps {
  items: BreakdownItem[]
  showFavicon?: boolean
}

export function BreakdownList({ items, showFavicon = true }: BreakdownListProps) {
  const maxValue = Math.max(...items.map((item) => item.value))

  return (
    <div className="space-y-2">
      {items.map((item, index) => (
        <div
          key={index}
          className="breakdown-item relative overflow-hidden"
        >
          {/* Background bar */}
          <div
            className="item-bar"
            style={{ width: `${(item.value / maxValue) * 100}%` }}
          />

          {/* Content */}
          <div className="relative flex items-center justify-between w-full">
            <div className="item-label">
              {showFavicon && (
                <img
                  src={`https://www.google.com/s2/favicons?domain=${item.label}&sz=32`}
                  alt=""
                  className="w-4 h-4 rounded"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none'
                  }}
                />
              )}
              <span className="truncate max-w-[120px]">{item.label}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="item-value">{formatNumber(item.value)}</span>
              <span className="text-xs text-foreground/40 w-10 text-right">
                {item.percentage}%
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
