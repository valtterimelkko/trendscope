'use client'

import { useEffect } from 'react'
import { X, MoreHorizontal, User, Calendar, Tag, Link2 } from 'lucide-react'

interface SidePeekProps {
  isOpen: boolean
  onClose: () => void
  issue?: {
    id: string
    title: string
    description?: string
    status: string
    priority: string
    assignee?: string
    dueDate?: string
    labels?: string[]
  }
}

export function SidePeek({ isOpen, onClose, issue }: SidePeekProps) {
  // Close on escape
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    if (isOpen) {
      document.addEventListener('keydown', down)
    }
    return () => document.removeEventListener('keydown', down)
  }, [isOpen, onClose])

  if (!isOpen || !issue) return null

  return (
    <>
      <div className="side-peek-backdrop" onClick={onClose} />
      <div className="side-peek">
        {/* Header */}
        <div className="sticky top-0 bg-surface border-b border-border px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-text-muted font-mono">PROD-{issue.id}</span>
            <button className="btn-ghost p-1">
              <Link2 className="h-4 w-4" />
            </button>
          </div>
          <div className="flex items-center gap-1">
            <button className="btn-ghost p-1.5">
              <MoreHorizontal className="h-4 w-4" />
            </button>
            <button onClick={onClose} className="btn-ghost p-1.5">
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Title */}
          <h2 className="text-xl font-semibold mb-6">{issue.title}</h2>

          {/* Metadata */}
          <div className="space-y-4 mb-6">
            <div className="flex items-center gap-4">
              <span className="w-24 text-sm text-text-muted">Status</span>
              <button className={`status-${issue.status}`}>
                {issue.status.charAt(0).toUpperCase() + issue.status.slice(1)}
              </button>
            </div>

            <div className="flex items-center gap-4">
              <span className="w-24 text-sm text-text-muted">Priority</span>
              <button className="btn-ghost text-sm px-2 py-1">
                {issue.priority.charAt(0).toUpperCase() + issue.priority.slice(1)}
              </button>
            </div>

            <div className="flex items-center gap-4">
              <span className="w-24 text-sm text-text-muted flex items-center gap-1">
                <User className="h-4 w-4" />
                Assignee
              </span>
              <button className="btn-ghost text-sm px-2 py-1">
                {issue.assignee || 'Unassigned'}
              </button>
            </div>

            <div className="flex items-center gap-4">
              <span className="w-24 text-sm text-text-muted flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                Due date
              </span>
              <button className="btn-ghost text-sm px-2 py-1">
                {issue.dueDate || 'No due date'}
              </button>
            </div>

            {issue.labels && issue.labels.length > 0 && (
              <div className="flex items-center gap-4">
                <span className="w-24 text-sm text-text-muted flex items-center gap-1">
                  <Tag className="h-4 w-4" />
                  Labels
                </span>
                <div className="flex gap-1">
                  {issue.labels.map((label) => (
                    <span key={label} className="px-2 py-0.5 bg-primary/20 text-primary text-xs rounded">
                      {label}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Description */}
          <div className="border-t border-border pt-6">
            <h3 className="text-sm font-medium mb-3">Description</h3>
            {issue.description ? (
              <div className="prose prose-sm prose-invert max-w-none">
                <p>{issue.description}</p>
              </div>
            ) : (
              <p className="text-sm text-text-muted">
                Add a description...
              </p>
            )}
          </div>

          {/* Activity */}
          <div className="border-t border-border pt-6 mt-6">
            <h3 className="text-sm font-medium mb-3">Activity</h3>
            <div className="space-y-4">
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-xs">
                  Y
                </div>
                <div className="flex-1">
                  <textarea
                    placeholder="Write a comment..."
                    className="input min-h-[80px] resize-none text-sm"
                  />
                  <button className="btn-primary text-sm mt-2">
                    Comment
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
