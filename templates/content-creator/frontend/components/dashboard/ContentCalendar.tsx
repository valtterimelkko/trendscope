'use client'

import { useState } from 'react'
import {
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  format,
  isSameMonth,
  isSameDay,
  addMonths,
  subMonths,
} from 'date-fns'
import { getStatusColor } from '@/lib/utils'

interface Post {
  id: string
  title: string
  status: string
  scheduled_for?: string
  published_at?: string
}

interface ContentCalendarProps {
  posts: Post[]
  onDateClick?: (date: Date) => void
  onPostClick?: (post: Post) => void
}

export function ContentCalendar({ posts, onDateClick, onPostClick }: ContentCalendarProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date())

  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(monthStart)
  const calendarStart = startOfWeek(monthStart)
  const calendarEnd = endOfWeek(monthEnd)

  const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd })

  const getPostsForDate = (date: Date) => {
    return posts.filter((post) => {
      const postDate = post.scheduled_for || post.published_at
      if (!postDate) return false
      return isSameDay(new Date(postDate), date)
    })
  }

  return (
    <div className="bg-surface border border-border rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-border">
        <h2 className="text-lg font-semibold text-foreground">
          {format(currentMonth, 'MMMM yyyy')}
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
            className="p-2 text-muted hover:text-foreground hover:bg-surface-hover rounded-lg transition-colors"
          >
            <ChevronLeftIcon className="w-5 h-5" />
          </button>
          <button
            onClick={() => setCurrentMonth(new Date())}
            className="px-3 py-1.5 text-sm font-medium text-muted hover:text-foreground hover:bg-surface-hover rounded-lg transition-colors"
          >
            Today
          </button>
          <button
            onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
            className="p-2 text-muted hover:text-foreground hover:bg-surface-hover rounded-lg transition-colors"
          >
            <ChevronRightIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Day headers */}
      <div className="grid grid-cols-7 border-b border-border">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
          <div
            key={day}
            className="px-3 py-2 text-xs font-medium text-muted uppercase tracking-wider text-center bg-surface-hover"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7">
        {days.map((day, index) => {
          const dayPosts = getPostsForDate(day)
          const isCurrentMonth = isSameMonth(day, currentMonth)
          const isToday = isSameDay(day, new Date())

          return (
            <div
              key={day.toString()}
              className={`min-h-[120px] p-2 border-b border-r border-border ${
                !isCurrentMonth ? 'bg-surface-hover' : 'bg-surface'
              } ${index % 7 === 6 ? 'border-r-0' : ''} hover:bg-surface-hover/50 cursor-pointer transition-colors`}
              onClick={() => onDateClick?.(day)}
            >
              <div className="flex items-center justify-between mb-1">
                <span
                  className={`w-7 h-7 flex items-center justify-center rounded-full text-sm ${
                    isToday
                      ? 'bg-primary text-white font-medium'
                      : isCurrentMonth
                      ? 'text-foreground'
                      : 'text-muted'
                  }`}
                >
                  {format(day, 'd')}
                </span>
              </div>

              {/* Posts for this day */}
              <div className="space-y-1">
                {dayPosts.slice(0, 3).map((post) => (
                  <div
                    key={post.id}
                    onClick={(e) => {
                      e.stopPropagation()
                      onPostClick?.(post)
                    }}
                    className={`calendar-event ${getStatusColor(post.status)}`}
                    title={post.title}
                  >
                    {post.title}
                  </div>
                ))}
                {dayPosts.length > 3 && (
                  <div className="text-xs text-muted px-1.5">
                    +{dayPosts.length - 3} more
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function ChevronLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
    </svg>
  )
}

function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  )
}
