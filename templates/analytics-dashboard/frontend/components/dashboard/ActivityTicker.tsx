'use client'

import { useEffect, useState } from 'react'
import { Globe, Clock } from 'lucide-react'

interface ActivityItem {
  id: string
  page: string
  country: string
  timestamp: Date
}

// Demo data - in production, this would come from WebSocket/real-time subscription
const generateDemoActivity = (): ActivityItem => {
  const pages = ['/home', '/pricing', '/features', '/blog', '/about', '/contact']
  const countries = ['US', 'UK', 'DE', 'FR', 'JP', 'CA', 'AU', 'NL']

  return {
    id: Math.random().toString(36).substring(7),
    page: pages[Math.floor(Math.random() * pages.length)],
    country: countries[Math.floor(Math.random() * countries.length)],
    timestamp: new Date(),
  }
}

export function ActivityTicker() {
  const [activities, setActivities] = useState<ActivityItem[]>([])

  useEffect(() => {
    // Initialize with some demo data
    const initial = Array.from({ length: 5 }, generateDemoActivity)
    setActivities(initial)

    // Simulate real-time updates
    const interval = setInterval(() => {
      setActivities((prev) => [generateDemoActivity(), ...prev.slice(0, 9)])
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  const formatTimeAgo = (date: Date) => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000)
    if (seconds < 60) return `${seconds}s ago`
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes}m ago`
    return `${Math.floor(minutes / 60)}h ago`
  }

  return (
    <div className="space-y-2 max-h-[300px] overflow-y-auto scrollbar-thin">
      {activities.map((activity, index) => (
        <div
          key={activity.id}
          className={`flex items-center gap-3 p-2 rounded-lg bg-surface text-sm ${
            index === 0 ? 'animate-slide-up' : ''
          }`}
        >
          <div className="flex items-center gap-2 text-foreground/60">
            <Globe className="h-4 w-4" />
            <span className="text-xs font-medium">{activity.country}</span>
          </div>
          <span className="truncate flex-1 font-medium">{activity.page}</span>
          <div className="flex items-center gap-1 text-foreground/40 text-xs">
            <Clock className="h-3 w-3" />
            {formatTimeAgo(activity.timestamp)}
          </div>
        </div>
      ))}
    </div>
  )
}
