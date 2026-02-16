'use client'

import { useState } from 'react'
import { Calendar, ChevronDown } from 'lucide-react'

const presets = [
  { label: 'Today', value: 'today' },
  { label: 'Last 7 days', value: '7d' },
  { label: 'Last 30 days', value: '30d' },
  { label: 'Last 90 days', value: '90d' },
  { label: 'This year', value: 'year' },
]

export function DateRangeController() {
  const [selected, setSelected] = useState('7d')
  const [isOpen, setIsOpen] = useState(false)

  const selectedLabel = presets.find((p) => p.value === selected)?.label

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg bg-background hover:bg-surface transition-colors"
      >
        <Calendar className="h-4 w-4 text-foreground/60" />
        <span className="font-medium text-sm">{selectedLabel}</span>
        <ChevronDown className={`h-4 w-4 text-foreground/60 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-48 bg-background border border-border rounded-lg shadow-lg z-20 py-1 animate-fade-in">
            {presets.map((preset) => (
              <button
                key={preset.value}
                onClick={() => {
                  setSelected(preset.value)
                  setIsOpen(false)
                }}
                className={`w-full px-4 py-2 text-left text-sm hover:bg-surface transition-colors ${
                  selected === preset.value
                    ? 'text-primary font-medium'
                    : 'text-foreground'
                }`}
              >
                {preset.label}
              </button>
            ))}

            <div className="border-t border-border my-1" />

            <button
              onClick={() => setIsOpen(false)}
              className="w-full px-4 py-2 text-left text-sm text-foreground/70 hover:bg-surface transition-colors"
            >
              Custom range...
            </button>
          </div>
        </>
      )}
    </div>
  )
}
